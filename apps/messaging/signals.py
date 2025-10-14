from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Message, Conversation

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsqu'un nouveau message est créé
    """
    if created:
        # Récupérer les destinataires (tous les participants sauf l'expéditeur)
        recipients = instance.conversation.participants.exclude(
            id=instance.sender.id
        )
        
        for recipient in recipients:
            # Vérifier si l'utilisateur a activé les notifications par email
            # (à implémenter dans le profil utilisateur)
            
            # Exemple : envoi d'email
            try:
                send_mail(
                    subject=f'Nouveau message de {instance.sender.username}',
                    message=f'{instance.sender.username} vous a envoyé un message:\n\n{instance.content[:100]}...',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Erreur d'envoi d'email: {e}")
            
            # Ici, vous pouvez aussi ajouter :
            # - Notification push (Firebase, OneSignal, etc.)
            # - Notification in-app
            # - Webhook vers un service externe


@receiver(post_save, sender=Message)
def update_conversation_timestamp(sender, instance, created, **kwargs):
    """
    Met à jour le timestamp de la conversation lors de l'ajout d'un message
    """
    if created:
        conversation = instance.conversation
        # La mise à jour automatique via auto_now devrait suffire,
        # mais on peut forcer si nécessaire
        conversation.save(update_fields=['updated_at'])


@receiver(post_save, sender=Conversation)
def log_conversation_creation(sender, instance, created, **kwargs):
    """
    Log la création d'une nouvelle conversation
    """
    if created:
        import logging
        logger = logging.getLogger('messaging')
        
        participants = ', '.join([p.username for p in instance.participants.all()])
        logger.info(f'Nouvelle conversation créée: ID={instance.id}, Participants={participants}')


@receiver(pre_delete, sender=Conversation)
def archive_before_delete(sender, instance, **kwargs):
    """
    Archive une conversation avant sa suppression
    """
    import logging
    from .utils import export_conversation_to_json
    
    logger = logging.getLogger('messaging')
    
    # Exporter les données
    try:
        data = export_conversation_to_json(instance)
        logger.info(f'Conversation {instance.id} archivée avant suppression: {data}')
    except Exception as e:
        logger.error(f'Erreur lors de l\'archivage de la conversation {instance.id}: {e}')


@receiver(post_save, sender=Message)
def detect_spam_message(sender, instance, created, **kwargs):
    """
    Détecte les messages potentiellement spam
    """
    if created:
        # Liste de mots-clés suspects (à personnaliser)
        spam_keywords = [
            'viagra', 'casino', 'lottery', 'winner',
            'click here', 'buy now', 'limited offer'
        ]
        
        content_lower = instance.content.lower()
        
        # Vérifier les mots-clés
        for keyword in spam_keywords:
            if keyword in content_lower:
                import logging
                logger = logging.getLogger('messaging')
                logger.warning(
                    f'Message potentiellement spam détecté: '
                    f'ID={instance.id}, Sender={instance.sender.username}, '
                    f'Keyword={keyword}'
                )
                
                # Optionnel : marquer le message ou notifier les admins
                # instance.is_spam = True
                # instance.save()
                break


@receiver(post_save, sender=Message)
def track_user_activity(sender, instance, created, **kwargs):
    """
    Enregistre l'activité de l'utilisateur
    """
    if created:
        # Mettre à jour le last_activity de l'utilisateur
        # (nécessite un champ last_activity dans le modèle User ou UserProfile)
        
        from django.utils import timezone
        user = instance.sender
        
        # Si vous avez un profil utilisateur avec last_activity
        if hasattr(user, 'profile'):
            user.profile.last_activity = timezone.now()
            user.profile.save(update_fields=['last_activity'])


@receiver(post_save, sender=Message)
def check_message_length(sender, instance, created, **kwargs):
    """
    Vérifie la longueur des messages et log les messages très longs
    """
    if created:
        max_normal_length = 1000
        
        if len(instance.content) > max_normal_length:
            import logging
            logger = logging.getLogger('messaging')
            logger.info(
                f'Message très long détecté: '
                f'ID={instance.id}, Length={len(instance.content)}'
            )


@receiver(post_save, sender=Conversation)
def create_welcome_message(sender, instance, created, **kwargs):
    """
    Crée un message de bienvenue automatique pour les nouvelles conversations
    """
    if created and instance.messages.count() == 0:
        # Créer un message système de bienvenue
        from .utils import create_system_message
        
        participants = ', '.join([p.username for p in instance.participants.all()])
        welcome_text = f"Conversation démarrée entre {participants}. Bonne discussion !"
        
        # Vous pouvez décommenter si vous voulez créer un message automatique
        # create_system_message(instance, welcome_text)


@receiver(post_save, sender=Message)
def auto_translate_message(sender, instance, created, **kwargs):
    """
    Traduction automatique des messages (optionnel)
    Nécessite une API de traduction (Google Translate, DeepL, etc.)
    """
    if created:
        # Exemple de logique de traduction
        # Si les utilisateurs ont des langues différentes
        pass
        
        # from googletrans import Translator
        # translator = Translator()
        # translated = translator.translate(instance.content, dest='fr')
        # instance.translated_content = translated.text
        # instance.save()


@receiver(post_save, sender=Message)
def moderate_content(sender, instance, created, **kwargs):
    """
    Modération automatique du contenu
    """
    if created:
        # Liste de mots interdits (à personnaliser)
        forbidden_words = ['insulte1', 'insulte2', 'mot_interdit']
        
        content_lower = instance.content.lower()
        
        for word in forbidden_words:
            if word in content_lower:
                import logging
                logger = logging.getLogger('messaging')
                logger.warning(
                    f'Contenu inapproprié détecté: '
                    f'ID={instance.id}, Sender={instance.sender.username}'
                )
                
                # Optionnel : modérer le message
                # instance.is_moderated = True
                # instance.content = "[Message modéré]"
                # instance.save()
                break


@receiver(post_save, sender=Message)
def send_realtime_notification(sender, instance, created, **kwargs):
    """
    Envoie une notification en temps réel via WebSocket
    """
    if created:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        conversation_group_name = f'chat_{instance.conversation.id}'
        
        # Notifier tous les participants via WebSocket
        # (déjà géré dans le consumer, mais on peut ajouter des notifications supplémentaires)
        
        # Exemple : envoyer une notification globale
        # async_to_sync(channel_layer.group_send)(
        #     'notifications',
        #     {
        #         'type': 'new_message_notification',
        #         'conversation_id': instance.conversation.id,
        #         'sender': instance.sender.username
        #     }
        # )


# N'oubliez pas d'importer les signaux dans apps.py
"""
# messaging/apps.py

from django.apps import AppConfig

class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    
    def ready(self):
        import messaging.signals  # Importer les signaux
"""