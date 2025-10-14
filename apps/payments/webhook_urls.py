from django.urls import path
from .webhooks import stripe_webhook, pi_webhook

urlpatterns = [
    path('stripe/', stripe_webhook, name='stripe-webhook'),
    path('pi/', pi_webhook, name='pi-webhook'),
]