"""
Webhook handlers for payment providers

TODO:
- Register webhook URLs in Stripe Dashboard: /webhooks/stripe/
- Register webhook URLs in Pi Network Dashboard: /webhooks/pi/
- Set webhook secrets in .env file
"""

import json
import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import Payment, EscrowTransaction
from .pi_provider import pi_provider


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    
    Important events:
    - payment_intent.succeeded: Payment authorized
    - payment_intent.payment_failed: Payment failed
    - charge.captured: Funds released from escrow
    - charge.refunded: Payment refunded
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_stripe_payment_succeeded(payment_intent)
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_stripe_payment_failed(payment_intent)
    
    elif event['type'] == 'charge.captured':
        charge = event['data']['object']
        handle_stripe_charge_captured(charge)
    
    elif event['type'] == 'charge.refunded':
        charge = event['data']['object']
        handle_stripe_charge_refunded(charge)
    
    return HttpResponse(status=200)


def handle_stripe_payment_succeeded(payment_intent):
    """Handle successful Stripe payment"""
    payment_intent_id = payment_intent['id']
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                provider_payment_id=payment_intent_id
            )
            
            if payment.status != 'succeeded':
                payment.status = 'succeeded'
                payment.succeeded_at = timezone.now()
                payment.save()
                
                # Create escrow
                auto_release_date = timezone.now() + timedelta(days=settings.AUTO_RELEASE_DAYS)
                EscrowTransaction.objects.get_or_create(
                    payment=payment,
                    defaults={
                        'status': 'held',
                        'auto_release_date': auto_release_date
                    }
                )
                
                # Update order
                order = payment.order
                order.status = 'paid_in_escrow'
                order.paid_at = timezone.now()
                order.save()
                
                print(f"Payment {payment.id} succeeded and held in escrow")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for payment_intent: {payment_intent_id}")


def handle_stripe_payment_failed(payment_intent):
    """Handle failed Stripe payment"""
    payment_intent_id = payment_intent['id']
    
    try:
        payment = Payment.objects.get(provider_payment_id=payment_intent_id)
        payment.status = 'failed'
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'cancelled'
        order.save()
        
        print(f"Payment {payment.id} failed")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for payment_intent: {payment_intent_id}")


def handle_stripe_charge_captured(charge):
    """Handle Stripe charge capture (escrow released)"""
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        return
    
    try:
        payment = Payment.objects.get(provider_payment_id=payment_intent_id)
        
        # Update escrow status
        if hasattr(payment, 'escrow'):
            escrow = payment.escrow
            escrow.status = 'released'
            escrow.released_at = timezone.now()
            escrow.save()
        
        # Update order status
        order = payment.order
        order.status = 'released'
        order.save()
        
        print(f"Escrow released for payment {payment.id}")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for payment_intent: {payment_intent_id}")


def handle_stripe_charge_refunded(charge):
    """Handle Stripe refund"""
    payment_intent_id = charge.get('payment_intent')
    
    if not payment_intent_id:
        return
    
    try:
        payment = Payment.objects.get(provider_payment_id=payment_intent_id)
        payment.status = 'refunded'
        payment.save()
        
        # Update escrow
        if hasattr(payment, 'escrow'):
            escrow = payment.escrow
            escrow.status = 'refunded'
            escrow.released_at = timezone.now()
            escrow.save()
        
        # Update order
        order = payment.order
        order.status = 'refunded'
        order.save()
        
        print(f"Payment {payment.id} refunded")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for payment_intent: {payment_intent_id}")


@csrf_exempt
@require_POST
def pi_webhook(request):
    """
    Handle Pi Network webhook events
    
    TODO: Implement real Pi Network webhook verification and handling
    """
    payload = request.body
    signature = request.META.get('HTTP_PI_SIGNATURE')
    
    # Verify signature
    if not pi_provider.verify_webhook_signature(payload, signature):
        return HttpResponse(status=400)
    
    try:
        data = json.loads(payload)
        event_type = data.get('type')
        payment_data = data.get('payment', {})
        
        if event_type == 'payment_completed':
            handle_pi_payment_completed(payment_data)
        
        elif event_type == 'payment_failed':
            handle_pi_payment_failed(payment_data)
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        print(f"Pi webhook error: {e}")
        return HttpResponse(status=400)


def handle_pi_payment_completed(payment_data):
    """Handle completed Pi Network payment"""
    payment_id = payment_data.get('payment_id')
    
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(
                provider_payment_id=payment_id
            )
            
            payment.status = 'succeeded'
            payment.succeeded_at = timezone.now()
            payment.metadata['transaction_id'] = payment_data.get('transaction_id')
            payment.save()
            
            # Create escrow
            auto_release_date = timezone.now() + timedelta(days=settings.AUTO_RELEASE_DAYS)
            EscrowTransaction.objects.get_or_create(
                payment=payment,
                defaults={
                    'status': 'held',
                    'auto_release_date': auto_release_date
                }
            )
            
            # Update order
            order = payment.order
            order.status = 'paid_in_escrow'
            order.paid_at = timezone.now()
            order.save()
            
            print(f"Pi payment {payment.id} completed")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for Pi payment_id: {payment_id}")


def handle_pi_payment_failed(payment_data):
    """Handle failed Pi Network payment"""
    payment_id = payment_data.get('payment_id')
    
    try:
        payment = Payment.objects.get(provider_payment_id=payment_id)
        payment.status = 'failed'
        payment.save()
        
        # Update order
        order = payment.order
        order.status = 'cancelled'
        order.save()
        
        print(f"Pi payment {payment.id} failed")
    
    except Payment.DoesNotExist:
        print(f"Payment not found for Pi payment_id: {payment_id}")