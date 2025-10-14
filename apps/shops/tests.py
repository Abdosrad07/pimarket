from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from apps.accounts.models import User
from .models import Shop, Product, ProductCategory, Order, OrderItem


class ShopModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            phone_number='+1234567890',
            display_name='Test User',
            is_phone_verified=True
        )
        
        self.shop = Shop.objects.create(
            owner=self.user,
            name='Test Shop',
            description='A test shop',
            address_text='123 Test St',
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_shop_creation(self):
        self.assertEqual(self.shop.name, 'Test Shop')
        self.assertEqual(self.shop.owner, self.user)
        self.assertFalse(self.shop.verified)


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            phone_number='+1234567890',
            display_name='Test User',
            is_phone_verified=True
        )
        
        self.shop = Shop.objects.create(
            owner=self.user,
            name='Test Shop',
            address_text='123 Test St',
            latitude=40.7128,
            longitude=-74.0060
        )
        
        self.category = ProductCategory.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            shop=self.shop,
            category=self.category,
            title='Test Product',
            description='A test product',
            price_fiat=Decimal('99.99'),
            price_pi=Decimal('31.41'),
            stock=10
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.title, 'Test Product')
        self.assertEqual(self.product.price_fiat, Decimal('99.99'))
        self.assertTrue(self.product.in_stock)
    
    def test_digital_product_always_in_stock(self):
        digital_product = Product.objects.create(
            shop=self.shop,
            title='Digital Product',
            description='A digital product',
            price_fiat=Decimal('19.99'),
            price_pi=Decimal('6.28'),
            is_digital=True,
            stock=0
        )
        self.assertTrue(digital_product.in_stock)


class OrderAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.buyer = User.objects.create(
            phone_number='+1234567890',
            display_name='Buyer',
            is_phone_verified=True
        )
        self.buyer.set_password('password123')
        self.buyer.save()
        
        self.seller = User.objects.create(
            phone_number='+0987654321',
            display_name='Seller',
            is_phone_verified=True
        )
        
        self.shop = Shop.objects.create(
            owner=self.seller,
            name='Test Shop',
            address_text='123 Test St',
            latitude=40.7128,
            longitude=-74.0060
        )
        
        self.product = Product.objects.create(
            shop=self.shop,
            title='Test Product',
            description='A test product',
            price_fiat=Decimal('99.99'),
            price_pi=Decimal('31.41'),
            stock=10
        )
    
    def test_create_order(self):
        self.client.force_authenticate(user=self.buyer)
        
        data = {
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2
                }
            ],
            'currency': 'fiat',
            'shipping_address': '456 Buyer St'
        }
        
        response = self.client.post('/api/shops/orders/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check order was created
        order = Order.objects.get(buyer=self.buyer)
        self.assertEqual(order.status, 'pending_payment')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_fiat, Decimal('199.98'))
        
        # Check stock was reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
    
    def test_insufficient_stock(self):
        self.client.force_authenticate(user=self.buyer)
        
        data = {
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 20  # More than available stock
                }
            ],
            'currency': 'fiat'
        }
        
        response = self.client.post('/api/shops/orders/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)