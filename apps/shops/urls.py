from django.urls import path
from . import views

app_name = 'shops'

urlpatterns = [
    # Shops
    path('', views.ShopListCreateView.as_view(), name='shop-list-create'),
    path('my-shops/', views.MyShopsListView.as_view(), name='my-shops'),
    path('my-products/', views.MyProductsListView.as_view(), name='my-products'),
    path('<int:pk>/', views.ShopDetailView.as_view(), name='shop-detail'),
    
    # Products
    path('<int:shop_id>/products/', views.ShopProductListCreateView.as_view(), name='shop-products'),
    path('products/<int:pk>/', views.ProductUpdateDeleteView.as_view(), name='product-detail-update-delete'),
    
    # Categories
    path('categories/', views.ProductCategoryListView.as_view(), name='category-list'),
    
    # Orders
    path('orders/create/', views.create_order, name='order-create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/confirm-delivery/', views.confirm_delivery, name='confirm-delivery'),
    path('orders/<int:order_id>/mark-shipped/', views.mark_as_shipped, name='mark-shipped'),
    
    # Buyer/Seller views
    path('buyer/orders/', views.BuyerOrderListView.as_view(), name='buyer-orders'),
    path('seller/orders/', views.SellerOrderListView.as_view(), name='seller-orders'),
    
    # Disputes
    path('disputes/', views.DisputeListView.as_view(), name='dispute-list'),
    path('disputes/open/', views.open_dispute, name='open-dispute'),
    path('disputes/<int:pk>/', views.DisputeDetailView.as_view(), name='dispute-detail'),
    path('disputes/<int:dispute_id>/messages/', views.add_dispute_message, name='add-dispute-message'),
]