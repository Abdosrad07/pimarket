from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
from apps.shops.models import Order
from .models import Payment, EscrowTransaction
from .stripe_provider import StripeProvider
from .pi_provider import pi_provider
from .serializers import PaymentSerializer


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment(request, order_id):
    """
    Create a payment for an order
    
    Supports Stripe (fiat) and Pi Network (pi) payments
    """
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    if order.status != 'pending_payment':
        return Response({
            'error': 'Order is not in pending payment status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    currency = order.currency
    
    try:
        with transaction.atomic():
            if currency == 'fiat':
                # Stripe payment
                amount_cents = int(order.total_fiat * 100)
                result = StripeProvider.create_payment_intent(order, amount_cents)
                
                if not result['success']:
                    return Response({
                        'error': result.get('error', 'Failed to create payment')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                payment = Payment.objects.create(
                    order=order,
                    provider='stripe',
                    provider_payment_id=result['payment_intent_id'],
                    amount_fiat=order.total_fiat,
                    amount_pi=0,
                    currency='fiat',
                    status='pending',
                    metadata={
                        'client_secret': result['client_secret']
                    }
                )
                
                return Response({
                    'payment': PaymentSerializer(payment).data,
                    'client_secret': result['client_secret'],
                    'publishable_key': StripeProvider.stripe.api_key  # For client-side
                })
            
            elif currency == 'pi':
                # Pi Network payment
                result = pi_provider.create_payment(order, order.total_pi)
                
                if not result['success']:
                    return Response({
                        'error': 'Failed to create Pi payment'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                payment = Payment.objects.create(
                    order=order,
                    provider='pi',
                    provider_payment_id=result['payment_id'],
                    amount_fiat=0,
                    amount_pi=order.total_pi,
                    currency='pi',
                    status='pending',
                    metadata={
                        'approval_url': result['approval_url']
                    }
                )
                
                return Response({
                    'payment': PaymentSerializer(payment).data,
                    'approval_url': result['approval_url'],
                    'message': 'Please approve the payment in your Pi app'
                })
            
            else:
                return Response({
                    'error': 'Mixed currency not yet supported'
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_stripe_payment(request):
    """
    Confirm Stripe payment after client-side confirmation
    
    This is called after user completes payment on frontend
    """
    payment_id = request.data.get('payment_id')
    
    if not payment_id:
        return Response({
            'error': 'payment_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    payment = get_object_or_404(Payment, id=payment_id, order__buyer=request.user)
    
    if payment.provider != 'stripe':
        return Response({
            'error': 'This endpoint is for Stripe payments only'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check payment status with Stripe
    result = StripeProvider.get_payment_status(payment.provider_payment_id)
    
    if not result['success']:
        return Response({
            'error': 'Failed to verify payment with Stripe'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if result['status'] == 'requires_capture':
        # Payment authorized, held in escrow
        with transaction.atomic():
            payment.status = 'succeeded'
            payment.succeeded_at = timezone.now()
            payment.save()
            
            # Create escrow transaction
            auto_release_date = timezone.now() + timedelta(days=7)  # Auto-release after 7 days
            EscrowTransaction.objects.create(
                payment=payment,
                status='held',
                auto_release_date=auto_release_date
            )
            
            # Update order status
            order = payment.order
            order.status = 'paid_in_escrow'
            order.paid_at = timezone.now()
            order.save()
            
            # Auto-release for digital products
            if all(item.product.is_digital for item in order.items.all()):
                from .tasks import release_escrow_funds
                release_escrow_funds.delay(order.id)
        
        return Response({
            'message': 'Payment confirmed and held in escrow',
            'payment': PaymentSerializer(payment).data
        })
    
    return Response({
        'error': f'Payment status is {result["status"]}',
        'status': result['status']
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_status(request, payment_id):
    """Get payment status"""
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        order__buyer=request.user
    )
    
    return Response({
        'payment': PaymentSerializer(payment).data
    })