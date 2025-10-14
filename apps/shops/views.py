from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import models
from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Shop, Product, ProductCategory, Order, OrderItem, Delivery, Dispute, DisputeMessage
from .serializers import (
    ShopSerializer, ProductSerializer, ProductListSerializer, ProductCategorySerializer,
    OrderSerializer, OrderCreateSerializer, DeliverySerializer, 
    DisputeSerializer, DisputeCreateSerializer, DisputeMessageSerializer
)

User = get_user_model()
from .filters import ProductFilter


class ShopListCreateView(generics.ListCreateAPIView):
    """List all shops or create a new shop"""
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class MyShopsListView(generics.ListAPIView):
    """
    Vue pour lister uniquement les boutiques appartenant à l'utilisateur authentifié.
    """
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Shop.objects.filter(owner=self.request.user)

class MyProductsListView(generics.ListAPIView):
    """Vue pour lister les produits des boutiques de l'utilisateur authentifié."""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated]
    # Laisser DRF utiliser la pagination par défaut définie dans settings.py
    
    def get_queryset(self):
        return Product.objects.filter(shop__owner=self.request.user).select_related('shop', 'category')


class ShopDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a shop"""
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only owner can update/delete"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Shop.objects.filter(owner=self.request.user)
        return Shop.objects.all()


class ProductCategoryListView(generics.ListAPIView):
    """List all product categories"""
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductListView(generics.ListAPIView):
    """List products with filters and proximity search"""
    queryset = Product.objects.filter(is_active=True).select_related('shop', 'category')
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price_fiat', 'price_pi']
    
    def get_serializer_context(self):
        """Pass user location to serializer for distance calculation"""
        context = super().get_serializer_context()
        context['user_lat'] = self.request.query_params.get('lat')
        context['user_lng'] = self.request.query_params.get('lng')
        return context


class ProductDetailView(generics.RetrieveAPIView):
    """Get product details"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer # Utilise maintenant le sérialiseur corrigé
    permission_classes = [permissions.AllowAny]


class ShopProductListCreateView(generics.ListCreateAPIView):
    """List products for a shop or create a new product"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        shop_id = self.kwargs['shop_id']
        return Product.objects.filter(shop_id=shop_id, is_active=True)
    
    def perform_create(self, serializer):
        shop_id = self.kwargs['shop_id']
        shop = get_object_or_404(Shop, id=shop_id, owner=self.request.user)
        serializer.save(shop=shop)


class ProductUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a product (owner only)"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(shop__owner=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order(request):
    """Create a new order from cart items"""
    serializer = OrderCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    items_data = serializer.validated_data['items']
    currency = serializer.validated_data['currency']
    
    try:
        with transaction.atomic():
            # Validate all products exist and belong to same shop
            product_ids = [item['product_id'] for item in items_data]
            products = Product.objects.select_for_update().filter(
                id__in=product_ids,
                is_active=True
            )
            
            if products.count() != len(product_ids):
                return Response({
                    'error': 'One or more products not found or inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check all products are from same shop
            shops = set(p.shop_id for p in products)
            if len(shops) > 1:
                return Response({
                    'error': 'All products must be from the same shop'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            shop = products.first().shop
            
            # Create order
            order = Order.objects.create(
                buyer=request.user,
                shop=shop,
                order_number=Order.generate_order_number(),
                currency=currency,
                status='created',
                shipping_address=serializer.validated_data.get('shipping_address', ''),
                shipping_latitude=serializer.validated_data.get('shipping_latitude'),
                shipping_longitude=serializer.validated_data.get('shipping_longitude'),
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Create order items and check stock
            for item_data in items_data:
                product = next(p for p in products if p.id == item_data['product_id'])
                quantity = item_data['quantity']
                
                # Check stock for physical products
                if not product.is_digital and product.stock < quantity:
                    raise Exception(f"Insufficient stock for {product.title}")
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price_fiat=product.price_fiat,
                    unit_price_pi=product.price_pi
                )
                
                # Reduce stock for physical products
                if not product.is_digital:
                    product.stock -= quantity
                    product.save()
            
            # Calculate totals
            order.calculate_total()
            
            # Update status to pending payment
            order.status = 'pending_payment'
            order.save()
            
            # Create delivery record for physical products
            has_physical = any(not p.is_digital for p in products)
            if has_physical:
                Delivery.objects.create(
                    order=order,
                    shipping_address=order.shipping_address,
                    shipping_latitude=order.shipping_latitude,
                    shipping_longitude=order.shipping_longitude
                )
            
            return Response({
                'order': OrderSerializer(order).data,
                'message': 'Order created successfully'
            }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(generics.RetrieveAPIView):
    """Get order details"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own orders or orders from their shops"""
        user = self.request.user
        return Order.objects.filter(
            models.Q(buyer=user) | models.Q(shop__owner=user)
        ).distinct()


class BuyerOrderListView(generics.ListAPIView):
    """List buyer's orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')


class SellerOrderListView(generics.ListAPIView):
    """List seller's orders"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'status']
    
    def get_queryset(self):
        return Order.objects.filter(
            shop__owner=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_delivery(request, order_id):
    """Buyer confirms delivery of order"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    if order.status != 'shipped':
        return Response({
            'error': 'Order must be shipped before confirming delivery'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from django.utils import timezone
    
    order.status = 'delivered'
    order.delivered_at = timezone.now()
    order.save()
    
    # Update delivery status
    if hasattr(order, 'delivery'):
        order.delivery.status = 'delivered'
        order.delivery.delivered_at = timezone.now()
        order.delivery.save()
    
    # Trigger payment release (will be handled by payment service)
    from apps.payments.tasks import release_escrow_funds
    release_escrow_funds.delay(order.id)
    
    return Response({
        'message': 'Delivery confirmed',
        'order': OrderSerializer(order).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_as_shipped(request, order_id):
    """Seller marks order as shipped"""
    order = get_object_or_404(Order, id=order_id, shop__owner=request.user)
    
    if order.status != 'paid_in_escrow':
        return Response({
            'error': 'Order must be paid before shipping'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from django.utils import timezone
    
    tracking_number = request.data.get('tracking_number', '')
    carrier = request.data.get('carrier', '')
    
    order.status = 'shipped'
    order.shipped_at = timezone.now()
    order.save()
    
    # Update delivery
    if hasattr(order, 'delivery'):
        order.delivery.tracking_number = tracking_number
        order.delivery.carrier = carrier
        order.delivery.status = 'in_transit'
        order.delivery.shipped_at = timezone.now()
        order.delivery.save()
    
    return Response({
        'message': 'Order marked as shipped',
        'order': OrderSerializer(order).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def open_dispute(request):
    """Open a dispute for an order"""
    serializer = DisputeCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order_id = serializer.validated_data['order_id']
    reason = serializer.validated_data['reason']
    
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    # Check if dispute already exists
    if hasattr(order, 'dispute'):
        return Response({
            'error': 'Dispute already exists for this order'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check order status
    if order.status not in ['paid_in_escrow', 'shipped', 'delivered']:
        return Response({
            'error': 'Cannot open dispute for this order status'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create dispute
    dispute = Dispute.objects.create(
        order=order,
        raised_by=request.user,
        reason=reason
    )
    
    # Update order status
    order.status = 'disputed'
    order.save()
    
    return Response({
        'message': 'Dispute opened',
        'dispute': DisputeSerializer(dispute).data
    }, status=status.HTTP_201_CREATED)


class DisputeListView(generics.ListAPIView):
    """List disputes"""
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q
        return Dispute.objects.filter(
            Q(raised_by=user) | Q(order__shop__owner=user)
        ).distinct()


class DisputeDetailView(generics.RetrieveAPIView):
    """Get dispute details"""
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q
        return Dispute.objects.filter(
            Q(raised_by=user) | Q(order__shop__owner=user)
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_dispute_message(request, dispute_id):
    """Add a message to a dispute"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Check user is involved in dispute
    user = request.user
    if user != dispute.raised_by and user != dispute.order.shop.owner:
        return Response({
            'error': 'You are not authorized to add messages to this dispute'
        }, status=status.HTTP_403_FORBIDDEN)
    
    message_text = request.data.get('message')
    if not message_text:
        return Response({
            'error': 'Message is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = DisputeMessage.objects.create(
        dispute=dispute,
        sender=user,
        message=message_text
    )
    
    return Response({
        'message': 'Message added',
        'data': DisputeMessageSerializer(message).data
    }, status=status.HTTP_201_CREATED)