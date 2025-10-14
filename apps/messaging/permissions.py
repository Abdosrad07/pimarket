from rest_framework import permissions

class IsConversationParticipant(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier que l'utilisateur
    fait partie de la conversation
    """
    
    def has_object_permission(self, request, view, obj):
        # Pour les objets Conversation
        if hasattr(obj, 'participants'):
            return obj.participants.filter(id=request.user.id).exists()
        
        # Pour les objets Message
        if hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(id=request.user.id).exists()
        
        return False


class IsMessageSenderOrRecipient(permissions.BasePermission):
    """
    Permission pour vérifier que l'utilisateur est soit l'expéditeur
    soit le destinataire du message
    """
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur est l'expéditeur
        if obj.sender == request.user:
            return True
        
        # L'utilisateur est un participant de la conversation
        return obj.conversation.participants.filter(id=request.user.id).exists()


class CanDeleteOwnMessage(permissions.BasePermission):
    """
    Permission pour supprimer uniquement ses propres messages
    dans un délai défini (ex: 15 minutes)
    """
    
    def has_object_permission(self, request, view, obj):
        from django.utils import timezone
        from datetime import timedelta
        
        # Seul l'expéditeur peut supprimer
        if obj.sender != request.user:
            return False
        
        # Vérifier le délai (15 minutes)
        time_limit = timezone.now() - timedelta(minutes=15)
        if obj.created_at < time_limit:
            return False
        
        return True