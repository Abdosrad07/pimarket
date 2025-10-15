from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from apps.shops.models import Product, Shop, Order, ProductCategory
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    """Vue pour la page d'accueil."""
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:6]
    stats = {
        'products_count': Product.objects.count(),
        'shops_count': Shop.objects.count(),
        'users_count': User.objects.count(),
        'orders_count': Order.objects.count(),
    }
    context = {
        'featured_products': featured_products,
        'stats': stats,
    }
    return render(request, 'home.html', context)

def account_dashboard(request):
    """Tableau de bord unifié pour l'utilisateur."""
    # La logique est maintenant gérée côté client avec JavaScript
    return render(request, 'auth/dashboard.html')

def buyer_dashboard(request):
    """Tableau de bord acheteur."""
    # Récupérer les 12 produits actifs les plus récents pour les afficher
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:12]
    
    context = {
        'recent_products': recent_products
    }
    return render(request, 'dashboard/buyer_dashboard.html', context)

def product_list(request):
    """Liste des produits avec filtres et pagination."""
    products = Product.objects.filter(is_active=True).select_related('shop', 'category')

    # Filtres
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(shop__name__icontains=search_query)
        )
    
    # Tri
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price_fiat')
    elif sort == 'price_desc':
        products = products.order_by('-price_fiat')
    else:
        products = products.order_by('-created_at')
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'login_url': 'login',

        'categories': ProductCategory.objects.all().order_by('name'),
    }
    return render(request, 'shops/product_list.html', context)

def product_detail(request, pk):
    """Détails d'un produit."""
    product = get_object_or_404(Product.objects.select_related('shop', 'category'), pk=pk, is_active=True)
    context = {'product': product}
    return render(request, 'shops/product_detail.html', context)

def shop_detail(request, pk):
    """Détails d'une boutique."""
    shop = get_object_or_404(Shop, pk=pk)
    product_list = Product.objects.filter(shop=shop, is_active=True).select_related('category').order_by('-created_at')
    
    paginator = Paginator(product_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'shop': shop,
        'products': page_obj,
    }
    return render(request, 'shops/shop_detail.html', context)

def create_shop(request):
    """Page pour créer une nouvelle boutique."""
    # La logique de création et d'authentification est gérée par l'API via JavaScript.
    # La vue sert uniquement à rendre le template.
    return render(request, 'shops/create_shop.html')
