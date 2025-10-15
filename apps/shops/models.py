from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Shop(models.Model):
    """Shop/Store model"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address_text = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model"""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price_fiat = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    price_pi = models.DecimalField(max_digits=10, decimal_places=7, validators=[MinValueValidator(Decimal('0.01'))])
    is_digital = models.BooleanField(default=False)
    digital_file_url = models.URLField(blank=True, help_text="URL for digital product download")
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.shop.name}"
    
    @property
    def in_stock(self):
        return self.stock > 0 or self.is_digital


class Order(models.Model):
    """Order model with escrow support"""
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('pending_payment', 'Pending Payment'),
        ('paid_in_escrow', 'Paid (In Escrow)'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('released', 'Released'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    CURRENCY_CHOICES = [
        ('fiat', 'Fiat'),
        ('pi', 'Pi'),
        ('mixed', 'Mixed'),
    ]
    
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    total_fiat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', db_index=True)
    
    shipping_address = models.TextField(blank=True)
    shipping_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    shipping_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['shop', 'status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.buyer.display_name}"
    
    @staticmethod
    def generate_order_number():
        import uuid
        return f"ORD-{uuid.uuid4().hex[:12].upper()}"
    
    def calculate_total(self):
        """Calculate order total from items"""
        items = self.items.all()
        self.total_fiat = sum(item.subtotal_fiat for item in items)
        self.total_pi = sum(item.subtotal_pi for item in items)
        self.save()


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price_fiat = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_pi = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_fiat = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_pi = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.quantity}x {self.product.title}"
    
    def save(self, *args, **kwargs):
        """Calculate subtotals before saving"""
        self.subtotal_fiat = self.unit_price_fiat * self.quantity
        self.subtotal_pi = self.unit_price_pi * self.quantity
        super().save(*args, **kwargs)


class Delivery(models.Model):
    """Delivery tracking for physical orders"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    shipping_address = models.TextField()
    shipping_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    shipping_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'
    
    def __str__(self):
        return f"Delivery for {self.order.order_number}"


class Dispute(models.Model):
    """Order dispute model"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='dispute')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dispute for {self.order.order_number}"


class DisputeMessage(models.Model):
    """Messages in a dispute thread"""
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Dispute Message'
        verbose_name_plural = 'Dispute Messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message by {self.sender.display_name} at {self.created_at}"