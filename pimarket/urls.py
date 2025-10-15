from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.shortcuts import render
from apps.core import views as core_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API endpoints
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/shops/', include('apps.shops.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/messaging/', include('apps.messaging.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Webhooks
    path('webhooks/', include('apps.payments.webhook_urls')),
    
    # Pages Web (Templates HTML)
    # Remplacer l'inclusion par des chemins directs pour plus de clarté
    path('', core_views.home, name='home'),
    path('products/', core_views.product_list, name='product_list'),
    path('products/<int:pk>/', core_views.product_detail, name='product_detail'),
    path('account/', core_views.account_dashboard, name='account_dashboard'),

    # Auth pages
    path('auth/login/', lambda request: render(request, 'auth/login.html'), name='login'),
    path('auth/register/', lambda request: render(request, 'auth/register.html'), name='register'),
    path('terms/', lambda request: render(request, 'auth/terms_of_service.html'), name='terms_of_service'),
    path('privacy/', lambda request: render(request, 'auth/privacy_policy.html'), name='privacy_policy'),


    # Shop and order pages
    path('shops/create/', core_views.create_shop, name='create_shop'),
    path('shops/<int:pk>/', core_views.shop_detail, name='shop_detail'),
    path('cart/', lambda request: render(request, 'orders/cart.html'), name='cart'),
    path('checkout/', lambda request: render(request, 'orders/checkout.html'), name='checkout'),
    path('orders/<int:order_id>/', lambda request, order_id: render(request, 'orders/order_detail.html', {'order_id': order_id}), name='order_detail'),
    
    # Dashboards
    path('dashboard/buyer/', core_views.buyer_dashboard, name='buyer_dashboard'),
    path('dashboard/seller/', lambda request: render(request, 'dashboard/seller_dashboard.html'), name='seller_dashboard'),

    # Racine
    path('', include('core.urls')), # cela met toutes les routes de core.urls à la racine

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)