from django.urls import path
from django.conf import settings
from django.views.static import serve
from .views import serve_text_file
import os   

urlpatterns = [
    path('validation-key.txt', serve, {'path': 'validation-key.txt', 'document_root': os.path.join(settings.BASE_DIR),}),
]