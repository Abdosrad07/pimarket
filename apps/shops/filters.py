import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Filter for products with category and shop filters"""
    category = django_filters.NumberFilter(field_name='category__id')
    shop = django_filters.NumberFilter(field_name='shop__id')
    min_price_fiat = django_filters.NumberFilter(field_name='price_fiat', lookup_expr='gte')
    max_price_fiat = django_filters.NumberFilter(field_name='price_fiat', lookup_expr='lte')
    min_price_pi = django_filters.NumberFilter(field_name='price_pi', lookup_expr='gte')
    max_price_pi = django_filters.NumberFilter(field_name='price_pi', lookup_expr='lte')
    is_digital = django_filters.BooleanFilter(field_name='is_digital')
    
    class Meta:
        model = Product
        fields = ['category', 'shop', 'is_digital']