from rest_framework import serializers
from .models import Shop, Product, ProductCategory, Order, OrderItem, Delivery, Dispute, DisputeMessage
from apps.accounts.serializers import UserSerializer


class ShopSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Shop
        fields = ['id', 'owner', 'name', 'description', 'address_text', 'latitude', 
                  'longitude', 'verified', 'products_count', 'created_at']
        read_only_fields = ['id', 'owner', 'verified', 'created_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'slug', 'description']


class ProductSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ['id', 'shop', 'shop_name', 'category', 'category_name', 
                  'category_id', 'title', 'description',
                  'price_fiat', 'price_pi', 'is_digital', 'stock', 'image', 
                  'in_stock', 'is_active', 'created_at']
        read_only_fields = ['id', 'shop', 'created_at', 'in_stock']


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified product serializer for list views"""
    shop_name = serializers.CharField(source='shop.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'title', 'price_fiat', 'price_pi', 'image', 'shop_name', 
                  'category_name', 'in_stock', 'distance', 'stock']
    
    def get_distance(self, obj):
        """Calculate distance if user location is provided in context"""
        user_lat = self.context.get('user_lat')
        user_lng = self.context.get('user_lng')
        
        if user_lat and user_lng:
            from math import radians, sin, cos, sqrt, atan2
            
            # Haversine formula
            R = 6371  # Earth radius in km
            
            lat1 = radians(float(user_lat))
            lon1 = radians(float(user_lng))
            lat2 = radians(float(obj.shop.latitude))
            lon2 = radians(float(obj.shop.longitude))
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return round(distance, 2)
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_title', 'product_image', 'quantity', 
                  'unit_price_fiat', 'unit_price_pi', 'subtotal_fiat', 'subtotal_pi']
        read_only_fields = ['id', 'subtotal_fiat', 'subtotal_pi']


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    items = OrderItemCreateSerializer(many=True)
    currency = serializers.ChoiceField(choices=['fiat', 'pi', 'mixed'])
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    shipping_latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    shipping_longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Order must contain at least one item")
        return items


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'tracking_number', 'carrier', 'status', 'shipping_address',
                  'shipped_at', 'delivered_at', 'notes']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    delivery = DeliverySerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'buyer', 'shop', 'items', 'total_fiat', 
                  'total_pi', 'currency', 'status', 'shipping_address', 
                  'shipping_latitude', 'shipping_longitude', 'notes', 'delivery',
                  'created_at', 'paid_at', 'shipped_at', 'delivered_at']
        read_only_fields = ['id', 'order_number', 'buyer', 'shop', 'total_fiat', 
                            'total_pi', 'created_at', 'paid_at', 'shipped_at', 'delivered_at']


class DisputeMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = DisputeMessage
        fields = ['id', 'sender', 'message', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class DisputeSerializer(serializers.ModelSerializer):
    raised_by = UserSerializer(read_only=True)
    messages = DisputeMessageSerializer(many=True, read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Dispute
        fields = ['id', 'order', 'order_number', 'raised_by', 'reason', 'status', 
                  'resolution', 'messages', 'created_at', 'resolved_at']
        read_only_fields = ['id', 'raised_by', 'created_at', 'resolved_at']


class DisputeCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField()