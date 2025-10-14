from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create/<int:order_id>/', views.create_payment, name='create-payment'),
    path('confirm/stripe/', views.confirm_stripe_payment, name='confirm-stripe'),
    path('<int:payment_id>/status/', views.payment_status, name='payment-status'),
]