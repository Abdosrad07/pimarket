from django.contrib import admin
from .models import Payment, EscrowTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'provider', 'status', 'amount_fiat', 'amount_pi', 'created_at']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['order__order_number', 'provider_payment_id']
    readonly_fields = ['created_at', 'updated_at', 'succeeded_at']
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('order', 'provider', 'provider_payment_id', 'status')
        }),
        ('Amounts', {
            'fields': ('amount_fiat', 'amount_pi', 'currency')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'succeeded_at')
        }),
    )


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    list_display = ['payment', 'status', 'held_at', 'auto_release_date', 'released_at']
    list_filter = ['status', 'held_at']
    search_fields = ['payment__order__order_number']
    readonly_fields = ['held_at', 'released_at']
    
    actions = ['release_escrow_manual']
    
    def release_escrow_manual(self, request, queryset):
        from .tasks import release_escrow_funds
        for escrow in queryset.filter(status='held'):
            release_escrow_funds.delay(escrow.payment.order.id)
        self.message_user(request, f"Triggered escrow release for {queryset.count()} transactions")
    release_escrow_manual.short_description = "Release selected escrow transactions"