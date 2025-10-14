from rest_framework import serializers
from .models import Payment, EscrowTransaction


class EscrowTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscrowTransaction
        fields = ['id', 'status', 'held_at', 'released_at', 'auto_release_date', 'notes']
        read_only_fields = ['id', 'held_at', 'released_at']


class PaymentSerializer(serializers.ModelSerializer):
    escrow = EscrowTransactionSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order', 'provider', 'provider_payment_id', 'amount_fiat', 
                  'amount_pi', 'currency', 'status', 'escrow', 'created_at', 
                  'succeeded_at', 'metadata']
        read_only_fields = ['id', 'order', 'provider', 'created_at', 'succeeded_at']