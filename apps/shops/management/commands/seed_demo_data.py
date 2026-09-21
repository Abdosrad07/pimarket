"""
Management command to seed demo data

Usage: python manage.py seed_demo_data

Idempotent: safe to run multiple times.

Demo accounts (password: demo1234):
- +221000000001  Alice Vendeuse (boutique Tech Paradise + Fashion Hub)
- +221000000002  Karim Acheteur
- admin / demo1234 pour le back-office /admin/
"""
from django.core.management.base import BaseCommand
from decimal import Decimal

from apps.accounts.models import User, UserLocation
from apps.shops.models import Shop, Product, ProductCategory, Order, OrderItem


DEMO_PASSWORD = 'demo1234'


class Command(BaseCommand):
    help = 'Seed database with idempotent demo data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding demo data...')

        # --- Users -----------------------------------------------------------
        buyer, buyer_created = User.objects.get_or_create(
            phone_number='+221000000002',
            defaults={'display_name': 'Karim Acheteur'},
        )
        if buyer_created:
            buyer.set_password(DEMO_PASSWORD)
        buyer.is_phone_verified = True
        buyer.is_active = True
        buyer.save()

        seller, seller_created = User.objects.get_or_create(
            phone_number='+221000000001',
            defaults={'display_name': 'Alice Vendeuse'},
        )
        if seller_created:
            seller.set_password(DEMO_PASSWORD)
        seller.is_phone_verified = True
        seller.is_active = True
        seller.save()

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                phone_number='+221000000000',
                password=DEMO_PASSWORD,
                display_name='Admin Pi Market',
            )
            self.stdout.write('Superuser created: +221000000000 / demo1234')

        if not UserLocation.objects.filter(user=buyer).exists():
            UserLocation.objects.create(
                user=buyer, latitude=40.7128, longitude=-74.0060,
                city='New York', country='USA', is_current=True,
            )
        if not UserLocation.objects.filter(user=seller).exists():
            UserLocation.objects.create(
                user=seller, latitude=40.7589, longitude=-73.9851,
                city='New York', country='USA', is_current=True,
            )

        # --- Categories ------------------------------------------------------
        categories = {}
        for name, slug, desc in [
            ('Electronics', 'electronics', 'Electronic devices and accessories'),
            ('Fashion', 'fashion', 'Clothing and accessories'),
            ('Digital Products', 'digital-products', 'E-books, courses, software'),
        ]:
            cat, _ = ProductCategory.objects.get_or_create(
                slug=slug, defaults={'name': name, 'description': desc},
            )
            categories[slug] = cat

        # --- Shops -----------------------------------------------------------
        shop1, _ = Shop.objects.get_or_create(
            owner=seller,
            name='Tech Paradise',
            defaults={
                'description': 'Your one-stop shop for electronics',
                'address_text': '123 Tech Street, New York, NY',
                'latitude': Decimal('40.758900'),
                'longitude': Decimal('-73.985100'),
                'verified': True,
            },
        )
        shop2, _ = Shop.objects.get_or_create(
            owner=seller,
            name='Fashion Hub',
            defaults={
                'description': 'Latest fashion trends',
                'address_text': '456 Fashion Ave, New York, NY',
                'latitude': Decimal('40.748900'),
                'longitude': Decimal('-73.968000'),
                'verified': True,
            },
        )

        # --- Products --------------------------------------------------------
        products_spec = [
            (shop1, 'electronics', 'Wireless Headphones',
             'High-quality Bluetooth headphones with noise cancellation',
             '99.99', '31.41', False, 50),
            (shop1, 'electronics', 'Smart Watch',
             'Fitness tracker with heart rate monitor',
             '199.99', '62.83', False, 30),
            (shop2, 'fashion', 'Designer T-Shirt',
             'Premium cotton t-shirt',
             '29.99', '9.42', False, 100),
            (shop2, 'fashion', 'Leather Jacket',
             'Genuine leather jacket',
             '299.99', '94.24', False, 20),
            (shop1, 'digital-products', 'Python Programming Course',
             'Complete Python course for beginners',
             '49.99', '15.70', True, 999),
            (shop1, 'digital-products', 'Web Development E-Book',
             'Learn modern web development',
             '19.99', '6.28', True, 999),
        ]
        products = []
        for shop, cat_slug, title, desc, fiat, pi, is_digital, stock in products_spec:
            product, _ = Product.objects.get_or_create(
                shop=shop,
                title=title,
                defaults={
                    'category': categories[cat_slug],
                    'description': desc,
                    'price_fiat': Decimal(fiat),
                    'price_pi': Decimal(pi),
                    'is_digital': is_digital,
                    'stock': stock,
                    'digital_file_url': 'https://example.com/download' if is_digital else '',
                },
            )
            products.append(product)

        # --- Demo product images ---------------------------------------------
        from apps.shops.product_art import ensure_product_images
        if ensure_product_images():
            self.stdout.write('Demo product images generated & attached')
        else:
            self.stdout.write(self.style.WARNING(
                'Pillow not installed - demo product images skipped'))
        if not Order.objects.filter(buyer=buyer).exists():
            product = products[0]
            order = Order.objects.create(
                buyer=buyer,
                shop=product.shop,
                order_number=Order.generate_order_number(),
                currency='fiat',
                status='created',
                shipping_address='789 Buyer Street, New York, NY',
                shipping_latitude=Decimal('40.712800'),
                shipping_longitude=Decimal('-74.006000'),
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=1,
                unit_price_fiat=product.price_fiat,
                unit_price_pi=product.price_pi,
            )
            order.calculate_total()
            self.stdout.write('Sample order created')

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write(f'Buyer:  {buyer.phone_number} / {DEMO_PASSWORD}')
        self.stdout.write(f'Seller: {seller.phone_number} / {DEMO_PASSWORD}')
        self.stdout.write(f'Admin:  +221000000000 / {DEMO_PASSWORD} (http://host:port/admin/)')
        self.stdout.write(f'{Product.objects.count()} products, {Shop.objects.count()} shops')
