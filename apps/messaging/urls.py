from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

app_name = 'messaging'

urlpatterns = [
    path('', include(router.urls)),
]

# Les URLs disponibles seront :
# GET    /api/conversations/              - Liste des conversations
# POST   /api/conversations/              - Créer une conversation
# GET    /api/conversations/{id}/         - Détails d'une conversation
# GET    /api/conversations/{id}/messages/ - Messages d'une conversation
# POST   /api/conversations/{id}/send_message/ - Envoyer un message
# GET    /api/conversations/unread_count/ - Nombre de messages non lus
# POST   /api/messages/                   - Créer un message
# POST   /api/messages/{id}/mark_read/    - Marquer comme lu
# POST   /api/messages/mark_conversation_read/ - Marquer conversation lue