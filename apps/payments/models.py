from django.db import models
from django.conf import settings
from apps.shops.models import Order


class Payment(models.Model):
    """Payment model for tracking all payment transactions"""
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('pi', 'Pi Network'),
        ('mock', 'Mock'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_payment_id = models.CharField(max_length=200, blank=True, db_index=True)
    
    amount_fiat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_pi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10)  # fiat, pi, mixed
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Metadata for provider-specific data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    succeeded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['provider', 'provider_payment_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.provider} - {self.status}"


class EscrowTransaction(models.Model):
    """Track escrow state for payments"""
    
    STATUS_CHOICES = [
        ('held', 'Held in Escrow'),
        ('released', 'Released to Seller'),
        ('refunded', 'Refunded to Buyer'),
    ]
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='escrow')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='held')
    
    held_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    auto_release_date = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Escrow Transaction'
        verbose_name_plural = 'Escrow Transactions'
        ordering = ['-held_at']
    
    def __str__(self):
        return f"Escrow for Payment {self.payment.id} - {self.status}"