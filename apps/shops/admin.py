from django.contrib import admin
from .models import Shop, Product, ProductCategory, Order, OrderItem, Delivery, Dispute, DisputeMessage


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['name', 'owner__phone_number', 'owner__display_name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['verify_shops']
    
    def verify_shops(self, request, queryset):
        queryset.update(verified=True)
    verify_shops.short_description = "Verify selected shops"


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'shop', 'price_fiat', 'price_pi', 'stock', 'is_digital', 'is_active']
    list_filter = ['is_digital', 'is_active', 'category', 'created_at']
    search_fields = ['title', 'shop__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price_fiat', 'unit_price_pi', 'subtotal_fiat', 'subtotal_pi']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'shop', 'status', 'total_fiat', 'total_pi', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['order_number', 'buyer__phone_number', 'shop__name']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'buyer', 'shop', 'status')
        }),
        ('Pricing', {
            'fields': ('total_fiat', 'total_pi', 'currency')
        }),
        ('Shipping', {
            'fields': ('shipping_address', 'shipping_latitude', 'shipping_longitude')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'shipped_at', 'delivered_at')
        }),
    )


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'tracking_number', 'carrier', 'shipped_at', 'delivered_at']
    list_filter = ['status', 'carrier']
    search_fields = ['order__order_number', 'tracking_number']
    readonly_fields = ['shipped_at', 'delivered_at']


class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 0
    readonly_fields = ['sender', 'message', 'created_at']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['order', 'raised_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'raised_by__phone_number']
    readonly_fields = ['created_at', 'resolved_at']
    inlines = [DisputeMessageInline]
    
    actions = ['resolve_disputes']
    
    def resolve_disputes(self, request, queryset):
        queryset.update(status='resolved')
    resolve_disputes.short_description = "Mark selected disputes as resolved"