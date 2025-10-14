"""
Management command to seed demo data

Usage: python manage.py seed_demo_data

Location: apps/shops/management/commands/seed_demo_data.py
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import User, UserLocation
from apps.shops.models import Shop, Product, ProductCategory, Order, OrderItem
from apps.payments.models import Payment, EscrowTransaction


class Command(BaseCommand):
    help = 'Seed database with demo data for testing'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding demo data...')
        
        # Create users
        self.stdout.write('Creating users...')
        buyer = User.objects.create(
            phone_number='+1234567890',
            display_name='John Buyer',
            is_phone_verified=True
        )
        buyer.set_password('password123')
        buyer.save()
        
        seller = User.objects.create(
            phone_number='+0987654321',
            display_name='Jane Seller',
            is_phone_verified=True
        )
        seller.set_password('password123')
        seller.save()
        
        # Create user locations
        UserLocation.objects.create(
            user=buyer,
            latitude=40.7128,
            longitude=-74.0060,
            city='New York',
            country='USA',
            is_current=True
        )
        
        UserLocation.objects.create(
            user=seller,
            latitude=40.7589,
            longitude=-73.9851,
            city='New York',
            country='USA',
            is_current=True
        )
        
        # Create categories
        self.stdout.write('Creating categories...')
        electronics = ProductCategory.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices and accessories'
        )
        
        fashion = ProductCategory.objects.create(
            name='Fashion',
            slug='fashion',
            description='Clothing and accessories'
        )
        
        digital = ProductCategory.objects.create(
            name='Digital Products',
            slug='digital-products',
            description='E-books, courses, software'
        )
        
        # Create shops
        self.stdout.write('Creating shops...')
        shop1 = Shop.objects.create(
            owner=seller,
            name='Tech Paradise',
            description='Your one-stop shop for electronics',
            address_text='123 Tech Street, New York, NY',
            latitude=40.7589,
            longitude=-73.9851,
            verified=True
        )
        
        shop2 = Shop.objects.create(
            owner=seller,
            name='Fashion Hub',
            description='Latest fashion trends',
            address_text='456 Fashion Ave, New York, NY',
            latitude=40.7489,
            longitude=-73.9680,
            verified=True
        )
        
        # Create products
        self.stdout.write('Creating products...')
        
        # Physical products
        Product.objects.create(
            shop=shop1,
            category=electronics,
            title='Wireless Headphones',
            description='High-quality Bluetooth headphones with noise cancellation',
            price_fiat=Decimal('99.99'),
            price_pi=Decimal('31.41'),
            is_digital=False,
            stock=50
        )
        
        Product.objects.create(
            shop=shop1,
            category=electronics,
            title='Smart Watch',
            description='Fitness tracker with heart rate monitor',
            price_fiat=Decimal('199.99'),
            price_pi=Decimal('62.83'),
            is_digital=False,
            stock=30
        )
        
        Product.objects.create(
            shop=shop2,
            category=fashion,
            title='Designer T-Shirt',
            description='Premium cotton t-shirt',
            price_fiat=Decimal('29.99'),
            price_pi=Decimal('9.42'),
            is_digital=False,
            stock=100
        )
        
        Product.objects.create(
            shop=shop2,
            category=fashion,
            title='Leather Jacket',
            description='Genuine leather jacket',
            price_fiat=Decimal('299.99'),
            price_pi=Decimal('94.24'),
            is_digital=False,
            stock=20
        )
        
        # Digital products
        Product.objects.create(
            shop=shop1,
            category=digital,
            title='Python Programming Course',
            description='Complete Python course for beginners',
            price_fiat=Decimal('49.99'),
            price_pi=Decimal('15.70'),
            is_digital=True,
            stock=999,
            digital_file_url='https://example.com/courses/python'
        )
        
        Product.objects.create(
            shop=shop1,
            category=digital,
            title='Web Development E-Book',
            description='Learn modern web development',
            price_fiat=Decimal('19.99'),
            price_pi=Decimal('6.28'),
            is_digital=True,
            stock=999,
            digital_file_url='https://example.com/ebooks/webdev'
        )
        
        # Create a sample order
        self.stdout.write('Creating sample order...')
        product = Product.objects.first()
        
        order = Order.objects.create(
            buyer=buyer,
            shop=product.shop,
            order_number=Order.generate_order_number(),
            currency='fiat',
            status='created',
            shipping_address='789 Buyer Street, New York, NY',
            shipping_latitude=40.7128,
            shipping_longitude=-74.0060
        )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            unit_price_fiat=product.price_fiat,
            unit_price_pi=product.price_pi
        )
        
        order.calculate_total()
        
        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write(f'Buyer: {buyer.phone_number} (password: password123)')
        self.stdout.write(f'Seller: {seller.phone_number} (password: password123)')
        self.stdout.write(f'Created {Product.objects.count()} products')
        self.stdout.write(f'Created {Order.objects.count()} order')