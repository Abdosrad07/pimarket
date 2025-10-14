from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from datetime import timedelta

def get_or_create_conversation(user1, user2, product=None):
    """
    Récupère ou crée une conversation entre deux utilisateurs
    
    Args:
        user1: Premier utilisateur
        user2: Deuxième utilisateur
        product: Produit associé (optionnel)
    
    Returns:
        Conversation object
    """
    # Chercher une conversation existante
    conversation = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(product=product)
        conversation.participants.add(user1, user2)
    
    return conversation


def send_message(conversation, sender, content, attachment=None):
    """
    Envoie un message dans une conversation
    
    Args:
        conversation: Objet Conversation
        sender: Utilisateur expéditeur
        content: Contenu du message
        attachment: Fichier attaché (optionnel)
    
    Returns:
        Message object
    """
    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=content,
        attachment=attachment
    )
    
    # Mettre à jour la date de modification de la conversation
    conversation.save()
    
    return message


def get_unread_conversations(user):
    """
    Récupère toutes les conversations avec des messages non lus
    
    Args:
        user: Utilisateur
    
    Returns:
        QuerySet de Conversations
    """
    return Conversation.objects.filter(
        participants=user,
        messages__is_read=False
    ).exclude(
        messages__sender=user
    ).distinct()


def get_total_unread_count(user):
    """
    Compte le nombre total de messages non lus pour un utilisateur
    
    Args:
        user: Utilisateur
    
    Returns:
        int: Nombre de messages non lus
    """
    return Message.objects.filter(
        conversation__participants=user,
        is_read=False
    ).exclude(sender=user).count()


def mark_conversation_as_read(conversation, user):
    """
    Marque tous les messages d'une conversation comme lus
    
    Args:
        conversation: Objet Conversation
        user: Utilisateur qui lit les messages
    """
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=user).update(is_read=True)


def delete_old_messages(days=365):
    """
    Supprime les messages plus anciens que X jours
    Utile pour le nettoyage automatique
    
    Args:
        days: Nombre de jours (défaut: 365)
    
    Returns:
        int: Nombre de messages supprimés
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = Message.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    return deleted_count


def get_user_conversations_with_stats(user):
    """
    Récupère les conversations d'un utilisateur avec statistiques
    
    Args:
        user: Utilisateur
    
    Returns:
        QuerySet avec annotations
    """
    from django.db.models import Count, Q, Max
    
    return Conversation.objects.filter(
        participants=user
    ).annotate(
        message_count=Count('messages'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
        ),
        last_message_date=Max('messages__created_at')
    ).order_by('-last_message_date')


def search_messages(user, query):
    """
    Recherche dans les messages de l'utilisateur
    
    Args:
        user: Utilisateur
        query: Texte à rechercher
    
    Returns:
        QuerySet de Messages
    """
    return Message.objects.filter(
        conversation__participants=user,
        content__icontains=query
    ).select_related('sender', 'conversation').order_by('-created_at')


def get_conversation_participants_except(conversation, user):
    """
    Récupère tous les participants d'une conversation sauf l'utilisateur spécifié
    
    Args:
        conversation: Objet Conversation
        user: Utilisateur à exclure
    
    Returns:
        QuerySet de Users
    """
    return conversation.participants.exclude(id=user.id)


def is_user_online(user, threshold_minutes=5):
    """
    Vérifie si un utilisateur est en ligne
    (basé sur sa dernière activité)
    
    Args:
        user: Utilisateur
        threshold_minutes: Seuil en minutes (défaut: 5)
    
    Returns:
        bool: True si en ligne
    """
    if not hasattr(user, 'last_activity'):
        return False
    
    threshold = timezone.now() - timedelta(minutes=threshold_minutes)
    return user.last_activity > threshold


def format_message_time(message):
    """
    Formate l'heure d'un message de manière lisible
    
    Args:
        message: Objet Message
    
    Returns:
        str: Temps formaté
    """
    now = timezone.now()
    diff = now - message.created_at
    
    if diff.days == 0:
        # Aujourd'hui
        if diff.seconds < 60:
            return "À l'instant"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} min"
        else:
            return message.created_at.strftime('%H:%M')
    elif diff.days == 1:
        return "Hier"
    elif diff.days < 7:
        days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return days[message.created_at.weekday()]
    else:
        return message.created_at.strftime('%d/%m/%Y')


def get_conversation_statistics(conversation):
    """
    Récupère des statistiques sur une conversation
    
    Args:
        conversation: Objet Conversation
    
    Returns:
        dict: Statistiques
    """
    from django.db.models import Count
    
    messages = conversation.messages.all()
    
    stats = {
        'total_messages': messages.count(),
        'unread_messages': messages.filter(is_read=False).count(),
        'messages_by_sender': {}
    }
    
    # Messages par expéditeur
    for participant in conversation.participants.all():
        count = messages.filter(sender=participant).count()
        stats['messages_by_sender'][participant.username] = count
    
    # Premier et dernier message
    if messages.exists():
        stats['first_message_date'] = messages.first().created_at
        stats['last_message_date'] = messages.last().created_at
    
    return stats


def notify_new_message(message):
    """
    Envoie une notification pour un nouveau message
    (à implémenter selon votre système de notifications)
    
    Args:
        message: Objet Message
    """
    # Exemple : envoyer un email, notification push, etc.
    recipients = message.conversation.participants.exclude(id=message.sender.id)
    
    for recipient in recipients:
        # Logique de notification
        print(f"Notification à {recipient.username}: Nouveau message de {message.sender.username}")
        # TODO: Implémenter l'envoi d'email ou notification push


def clean_message_content(content):
    """
    Nettoie et valide le contenu d'un message
    
    Args:
        content: Contenu du message
    
    Returns:
        str: Contenu nettoyé
    """
    import re
    
    # Supprimer les espaces en trop
    content = content.strip()
    
    # Supprimer les caractères de contrôle
    content = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', content)
    
    # Limiter la longueur
    max_length = 5000
    if len(content) > max_length:
        content = content[:max_length]
    
    return content


def export_conversation_to_json(conversation):
    """
    Exporte une conversation au format JSON
    
    Args:
        conversation: Objet Conversation
    
    Returns:
        dict: Données de la conversation
    """
    messages = conversation.messages.all()
    
    return {
        'conversation_id': conversation.id,
        'participants': [
            {
                'id': p.id,
                'username': p.username,
                'email': p.email
            }
            for p in conversation.participants.all()
        ],
        'created_at': conversation.created_at.isoformat(),
        'messages': [
            {
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'is_read': msg.is_read,
                'created_at': msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


def get_active_conversations(user, days=30):
    """
    Récupère les conversations actives (avec messages récents)
    
    Args:
        user: Utilisateur
        days: Nombre de jours (défaut: 30)
    
    Returns:
        QuerySet de Conversations
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    return Conversation.objects.filter(
        participants=user,
        messages__created_at__gte=cutoff_date
    ).distinct()


def archive_conversation(conversation):
    """
    Archive une conversation (ajouter un champ 'is_archived' au modèle si besoin)
    
    Args:
        conversation: Objet Conversation
    """
    # Si vous avez un champ is_archived dans votre modèle
    # conversation.is_archived = True
    # conversation.save()
    pass


def block_user(user, blocked_user):
    """
    Bloque un utilisateur (à implémenter avec un modèle BlockedUser)
    
    Args:
        user: Utilisateur qui bloque
        blocked_user: Utilisateur bloqué
    """
    # TODO: Créer un modèle BlockedUser si nécessaire
    # BlockedUser.objects.get_or_create(user=user, blocked=blocked_user)
    pass


def get_message_delivery_status(message):
    """
    Récupère le statut de livraison d'un message
    
    Args:
        message: Objet Message
    
    Returns:
        str: 'sent', 'delivered', 'read'
    """
    if message.is_read:
        return 'read'
    elif message.created_at < timezone.now() - timedelta(minutes=1):
        return 'delivered'
    else:
        return 'sent'


def generate_conversation_summary(conversation, max_messages=5):
    """
    Génère un résumé d'une conversation
    
    Args:
        conversation: Objet Conversation
        max_messages: Nombre maximum de messages à inclure
    
    Returns:
        dict: Résumé
    """
    recent_messages = conversation.messages.order_by('-created_at')[:max_messages]
    
    return {
        'conversation_id': conversation.id,
        'participants_count': conversation.participants.count(),
        'total_messages': conversation.messages.count(),
        'unread_messages': conversation.messages.filter(is_read=False).count(),
        'last_activity': conversation.updated_at,
        'recent_messages': [
            {
                'sender': msg.sender.username,
                'content_preview': msg.content[:100],
                'created_at': msg.created_at
            }
            for msg in recent_messages
        ]
    }


def validate_message_attachment(file):
    """
    Valide un fichier attaché à un message
    
    Args:
        file: Fichier uploadé
    
    Returns:
        tuple: (bool, str) - (Valide, Message d'erreur)
    """
    # Taille maximale: 10 MB
    max_size = 10 * 1024 * 1024
    
    if file.size > max_size:
        return False, "Le fichier est trop volumineux (max 10 MB)"
    
    # Extensions autorisées
    allowed_extensions = [
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 
        'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip'
    ]
    
    file_extension = file.name.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        return False, f"Extension {file_extension} non autorisée"
    
    return True, "OK"


def get_conversation_between_users(user1_id, user2_id):
    """
    Trouve une conversation entre deux utilisateurs par leurs IDs
    
    Args:
        user1_id: ID du premier utilisateur
        user2_id: ID du second utilisateur
    
    Returns:
        Conversation ou None
    """
    try:
        return Conversation.objects.filter(
            participants__id=user1_id
        ).filter(
            participants__id=user2_id
        ).first()
    except Exception:
        return None


def bulk_mark_as_read(user, conversation_ids):
    """
    Marque plusieurs conversations comme lues
    
    Args:
        user: Utilisateur
        conversation_ids: Liste des IDs de conversations
    """
    Message.objects.filter(
        conversation_id__in=conversation_ids,
        is_read=False
    ).exclude(sender=user).update(is_read=True)


def get_popular_contacts(user, limit=10):
    """
    Récupère les contacts les plus fréquents d'un utilisateur
    
    Args:
        user: Utilisateur
        limit: Nombre de contacts à retourner
    
    Returns:
        List de tuples (User, message_count)
    """
    from django.db.models import Count
    
    conversations = Conversation.objects.filter(participants=user)
    
    contact_counts = {}
    for conv in conversations:
        other_participants = conv.participants.exclude(id=user.id)
        message_count = conv.messages.count()
        
        for participant in other_participants:
            if participant.id not in contact_counts:
                contact_counts[participant.id] = {
                    'user': participant,
                    'count': 0
                }
            contact_counts[participant.id]['count'] += message_count
    
    sorted_contacts = sorted(
        contact_counts.values(),
        key=lambda x: x['count'],
        reverse=True
    )[:limit]
    
    return [(c['user'], c['count']) for c in sorted_contacts]


def create_system_message(conversation, content):
    """
    Crée un message système (ex: "Jean a rejoint la conversation")
    
    Args:
        conversation: Objet Conversation
        content: Contenu du message
    
    Returns:
        Message object
    """
    # Utiliser un utilisateur système ou le premier participant
    system_user = conversation.participants.first()
    
    return Message.objects.create(
        conversation=conversation,
        sender=system_user,
        content=f"[SYSTÈME] {content}",
        is_read=True
    )


def get_conversation_activity_timeline(conversation):
    """
    Génère une timeline d'activité pour une conversation
    
    Args:
        conversation: Objet Conversation
    
    Returns:
        List de dict avec les événements
    """
    from django.db.models.functions import TruncDate
    from django.db.models import Count
    
    # Messages par jour
    daily_activity = conversation.messages.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    return list(daily_activity)


def get_user_messaging_stats(user):
    """
    Récupère des statistiques globales de messagerie pour un utilisateur
    
    Args:
        user: Utilisateur
    
    Returns:
        dict: Statistiques
    """
    conversations = Conversation.objects.filter(participants=user)
    sent_messages = Message.objects.filter(sender=user)
    received_messages = Message.objects.filter(
        conversation__participants=user
    ).exclude(sender=user)
    
    return {
        'total_conversations': conversations.count(),
        'active_conversations': get_active_conversations(user).count(),
        'total_messages_sent': sent_messages.count(),
        'total_messages_received': received_messages.count(),
        'unread_messages': get_total_unread_count(user),
        'average_response_time': calculate_average_response_time(user),
        'most_active_conversation': get_most_active_conversation(user)
    }


def calculate_average_response_time(user):
    """
    Calcule le temps de réponse moyen de l'utilisateur
    
    Args:
        user: Utilisateur
    
    Returns:
        timedelta ou None
    """
    from django.db.models import F, ExpressionWrapper, DurationField
    
    # Messages de l'utilisateur
    user_messages = Message.objects.filter(sender=user).order_by('created_at')
    
    if user_messages.count() < 2:
        return None
    
    total_time = timedelta()
    response_count = 0
    
    for conv in Conversation.objects.filter(participants=user):
        messages = list(conv.messages.order_by('created_at'))
        
        for i in range(1, len(messages)):
            prev_msg = messages[i-1]
            curr_msg = messages[i]
            
            # Si le message actuel est de l'utilisateur et le précédent n'est pas de lui
            if curr_msg.sender == user and prev_msg.sender != user:
                time_diff = curr_msg.created_at - prev_msg.created_at
                total_time += time_diff
                response_count += 1
    
    if response_count == 0:
        return None
    
    return total_time / response_count


def get_most_active_conversation(user):
    """
    Trouve la conversation la plus active de l'utilisateur
    
    Args:
        user: Utilisateur
    
    Returns:
        Conversation ou None
    """
    from django.db.models import Count
    
    return Conversation.objects.filter(
        participants=user
    ).annotate(
        msg_count=Count('messages')
    ).order_by('-msg_count').first()


def sanitize_html_content(content):
    """
    Nettoie le contenu HTML pour éviter les attaques XSS
    
    Args:
        content: Contenu potentiellement dangereux
    
    Returns:
        str: Contenu nettoyé
    """
    import html
    
    # Échapper tous les caractères HTML
    return html.escape(content)


def create_conversation_backup(conversation, backup_path):
    """
    Crée une sauvegarde d'une conversation
    
    Args:
        conversation: Objet Conversation
        backup_path: Chemin du fichier de sauvegarde
    """
    import json
    
    data = export_conversation_to_json(conversation)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

User = get_user_model()