"""
Celery tasks for payment processing

These tasks handle:
- Checking pending payments
- Auto-releasing escrow funds
- Sending payment notifications
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import Payment, EscrowTransaction
from apps.shops.models import Order
from .stripe_provider import StripeProvider


@shared_task
def check_pending_payments():
    """
    Check status of pending payments
    
    Runs every 10 minutes (configured in celery.py)
    """
    pending_payments = Payment.objects.filter(
        status='pending',
        created_at__gte=timezone.now() - timedelta(hours=24)
    )
    
    for payment in pending_payments:
        if payment.provider == 'stripe':
            result = StripeProvider.get_payment_status(payment.provider_payment_id)
            
            if result['success']:
                if result['status'] == 'requires_capture':
                    # Payment succeeded, update status
                    with transaction.atomic():
                        payment.status = 'succeeded'
                        payment.succeeded_at = timezone.now()
                        payment.save()
                        
                        # Create escrow
                        auto_release_date = timezone.now() + timedelta(days=7)
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
                        
                        print(f"Payment {payment.id} updated to succeeded")
                
                elif result['status'] == 'canceled':
                    payment.status = 'failed'
                    payment.save()
                    
                    order = payment.order
                    order.status = 'cancelled'
                    order.save()
    
    return f"Checked {pending_payments.count()} pending payments"


@shared_task
def auto_release_escrow():
    """
    Auto-release escrow funds after specified period
    
    Runs daily at midnight (configured in celery.py)
    """
    escrows_to_release = EscrowTransaction.objects.filter(
        status='held',
        auto_release_date__lte=timezone.now()
    )
    
    released_count = 0
    
    for escrow in escrows_to_release:
        order = escrow.payment.order
        
        # Only auto-release if order is delivered or shipped
        if order.status in ['delivered', 'shipped']:
            success = release_escrow_funds.apply(args=[order.id]).get()
            if success:
                released_count += 1
    
    return f"Auto-released {released_count} escrow transactions"


@shared_task
def release_escrow_funds(order_id):
    """
    Release escrow funds to seller
    
    Called when:
    - Buyer confirms delivery
    - Auto-release period expires
    - Digital product auto-release
    """
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            
            # Get payment
            payment = order.payments.filter(status='succeeded').first()
            
            if not payment:
                print(f"No successful payment found for order {order_id}")
                return False
            
            # Check if escrow exists
            if not hasattr(payment, 'escrow'):
                print(f"No escrow found for payment {payment.id}")
                return False
            
            escrow = payment.escrow
            
            if escrow.status != 'held':
                print(f"Escrow already {escrow.status}")
                return False
            
            # Release funds based on provider
            if payment.provider == 'stripe':
                result = StripeProvider.capture_payment(payment.provider_payment_id)
                
                if not result['success']:
                    print(f"Failed to capture Stripe payment: {result.get('error')}")
                    return False
            
            elif payment.provider == 'pi':
                # Pi Network doesn't need capture - funds already transferred
                pass
            
            # Update escrow status
            escrow.status = 'released'
            escrow.released_at = timezone.now()
            escrow.save()
            
            # Update order status
            order.status = 'released'
            order.save()
            
            print(f"Escrow released for order {order.order_number}")
            
            # TODO: Send notification to seller
            # send_seller_notification.delay(order.id)
            
            return True
    
    except Order.DoesNotExist:
        print(f"Order {order_id} not found")
        return False
    
    except Exception as e:
        print(f"Error releasing escrow for order {order_id}: {e}")
        return False


@shared_task
def refund_order(order_id, reason=None):
    """
    Refund an order (e.g., after dispute resolution)
    """
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            
            # Get payment
            payment = order.payments.filter(status='succeeded').first()
            
            if not payment:
                print(f"No successful payment found for order {order_id}")
                return False
            
            # Refund based on provider
            if payment.provider == 'stripe':
                result = StripeProvider.refund_payment(
                    payment.provider_payment_id,
                    reason=reason
                )
                
                if not result['success']:
                    print(f"Failed to refund Stripe payment: {result.get('error')}")
                    return False
            
            elif payment.provider == 'pi':
                # TODO: Implement Pi Network refund if supported
                pass
            
            # Update payment status
            payment.status = 'refunded'
            payment.save()
            
            # Update escrow
            if hasattr(payment, 'escrow'):
                escrow = payment.escrow
                escrow.status = 'refunded'
                escrow.released_at = timezone.now()
                escrow.notes = reason or 'Refunded'
                escrow.save()
            
            # Update order status
            order.status = 'refunded'
            order.save()
            
            print(f"Order {order.order_number} refunded")
            
            # TODO: Send notification to buyer
            # send_buyer_notification.delay(order.id)
            
            return True
    
    except Order.DoesNotExist:
        print(f"Order {order_id} not found")
        return False
    
    except Exception as e:
        print(f"Error refunding order {order_id}: {e}")
        return False


@shared_task
def send_payment_notification(payment_id, notification_type):
    """
    Send payment-related notifications
    
    TODO: Implement SMS/Email notifications
    """
    # Placeholder for notification logic
    try:
        payment = Payment.objects.get(id=payment_id)
        order = payment.order
        
        if notification_type == 'payment_succeeded':
            message = f"Payment successful for order {order.order_number}"
            # TODO: Send SMS to buyer
            # send_sms(order.buyer.phone_number, message)
        
        elif notification_type == 'escrow_released':
            message = f"Payment released for order {order.order_number}"
            # TODO: Send SMS to seller
            # send_sms(order.shop.owner.phone_number, message)
        
        print(f"Notification sent: {message}")
        return True
    
    except Payment.DoesNotExist:
        print(f"Payment {payment_id} not found")
        return False