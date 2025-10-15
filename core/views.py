from django.http import HttpResponse, Http404
from django.conf import settings
import os

def serve_text_file(request):
    file_path = os.path.join(settings.BASE_DIR, 'static', 'validation-key.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return HttpResponse(content, content_type='text/plain')
    else:
        raise Http404("File not found")