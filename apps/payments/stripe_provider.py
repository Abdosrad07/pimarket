"""
Stripe Payment Provider

Handles Stripe payment integration with escrow logic simulation.

TODO for Production:
- Replace test keys with live keys in .env
- Implement proper Stripe Connect for seller payouts
- Set up webhook endpoints in Stripe Dashboard
- Enable 3D Secure for card payments
- Implement proper error handling and retries
"""

import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeProvider:
    """Stripe payment provider with escrow simulation"""
    
    @staticmethod
    def create_payment_intent(order, amount_cents):
        """
        Create a Stripe PaymentIntent for an order
        
        Args:
            order: Order instance
            amount_cents: Amount in cents (smallest currency unit)
        
        Returns:
            dict: PaymentIntent data including client_secret
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',  # TODO: Make currency configurable
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'buyer_id': order.buyer.id,
                    'shop_id': order.shop.id,
                },
                capture_method='manual',  # Hold funds for escrow
                description=f'Order {order.order_number}',
            )
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }
        
    @staticmethod
    def confirm_payment(payment_intent_id):
        """
        Confirm a PaymentIntent (client-side confirmation)
        
        In real implementation, this would be done client-side via Stripe.js
        """
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def capture_payment(payment_intent_id, amount_to_capture=None):
        """
        Capture a payment (release from escrow)
        
        This is called when order is delivered and confirmed by buyer
        """
        try:
            intent = stripe.PaymentIntent.capture(
                payment_intent_id,
                amount_to_capture=amount_to_capture
            )
            
            return {
                'success': True,
                'status': intent.status,
                'amount_received': intent.amount_received,
            }
        
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def refund_payment(payment_intent_id, amount=None, reason=None):
        """
        Refund a payment (e.g., dispute resolved in buyer's favor)
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            amount: Amount to refund in cents (None = full refund)
            reason: Refund reason
        """
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=amount,
                reason=reason or 'requested_by_customer',
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status,
            }
        
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def cancel_payment(payment_intent_id):
        """Cancel a PaymentIntent (before capture)"""
        try:
            intent = stripe.PaymentIntent.cancel(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    @staticmethod
    def get_payment_status(payment_intent_id):
        """Get current status of a PaymentIntent"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
                'amount': intent.amount,
                'amount_received': intent.amount_received,
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e),
            }