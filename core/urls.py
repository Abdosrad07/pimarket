from django.urls import path
from .views import serve_text_file

urlpatterns = [
    path('<str:filename>', serve_text_file, name='serve_text_file'),
]