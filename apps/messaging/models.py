from django.db import models
from django.conf import settings
from django.utils import timezone

class Conversation(models.Model):
    """Représente une conversation entre deux utilisateurs"""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optionnel : lier à un produit spécifique
    product = models.ForeignKey('shops.Product', on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='conversations')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        users = ', '.join([user.username for user in self.participants.all()])
        return f"Conversation: {users}"
    
    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_last_message(self):
        """Retourne le dernier message de la conversation"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """Représente un message dans une conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, 
                                     related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optionnel : pour les fichiers joints
    attachment = models.FileField(upload_to='message_attachments/', 
                                  null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    def mark_as_read(self):
        """Marque le message comme lu"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class MessageReadStatus(models.Model):
    """Suivi du statut de lecture des messages par utilisateur"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, 
                                related_name='read_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
        verbose_name_plural = 'Message read statuses'