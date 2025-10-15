from django.urls import path
from .views import serve_text_file

urlpatterns = [
    path('validation-key', serve_text_file, name='validation_key'),
]