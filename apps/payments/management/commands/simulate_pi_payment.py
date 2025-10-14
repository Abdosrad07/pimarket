"""
Management command to simulate Pi Network payment completion

Usage: python manage.py simulate_pi_payment --order <order_id>

Location: apps/payments/management/commands/simulate_pi_payment.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from apps.shops.models import Order
from apps.payments.models import Payment, EscrowTransaction


class Command(BaseCommand):
    help = 'Simulate Pi Network payment completion for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='The ID of the order to simulate payment for')
    
    def handle(self, *args, **options):
        order_id = options['order_id']
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order {order_id} not found'))
            return
        
        # Check if order has pending Pi payment
        payment = Payment.objects.filter(
            order=order,
            provider='pi',
            status='pending'
        ).first()
        
        if not payment:
            self.stdout.write(self.style.ERROR(
                f'No pending Pi payment found for order {order.order_number}'
            ))
            return
        
        # Simulate payment completion
        with transaction.atomic():
            payment.status = 'succeeded'
            payment.succeeded_at = timezone.now()
            payment.metadata['simulated'] = True
            payment.metadata['transaction_id'] = f'pi_sim_{order.id}'
            payment.save()
            
            # Create escrow
            auto_release_date = timezone.now() + timedelta(days=7)
            escrow, created = EscrowTransaction.objects.get_or_create(
                payment=payment,
                defaults={
                    'status': 'held',
                    'auto_release_date': auto_release_date
                }
            )
            
            # Update order status
            order.status = 'paid_in_escrow'
            order.paid_at = timezone.now()
            order.save()
            
            # Auto-release for digital products
            if all(item.product.is_digital for item in order.items.all()):
                from apps.payments.tasks import release_escrow_funds
                release_escrow_funds.delay(order.id)
                self.stdout.write(self.style.SUCCESS(
                    'Digital product - escrow will be auto-released'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Pi payment simulated for order {order.order_number}'
        ))
        self.stdout.write(f'Payment ID: {payment.id}')
        self.stdout.write(f'Status: {payment.status}')
        self.stdout.write(f'Order Status: {order.status}')