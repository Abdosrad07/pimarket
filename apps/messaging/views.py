from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, OuterRef, Subquery, Count, F, Value
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from .serializers import (
    ConversationSerializer, 
    MessageSerializer, 
    ConversationCreateSerializer
)

# Vue template pour l'interface
User = get_user_model()

@login_required
def messages_view(request):
    """
    Vue principale pour l'interface de messagerie
    """
    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.objects.filter(participants=request.user).prefetch_related('participants', 'messages').order_by('-updated_at')
    
    active_conversation = None
    messages = []
    
    # Tenter de démarrer une nouvelle conversation
    recipient_id = request.GET.get('start_with')
    if recipient_id:
        try:
            recipient = User.objects.get(id=recipient_id)
            # Chercher une conversation existante
            active_conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
            if not active_conversation:
                # Créer une nouvelle conversation
                active_conversation = Conversation.objects.create()
                active_conversation.participants.add(request.user, recipient)
            # Rediriger vers l'URL propre de la conversation
            return redirect(f"{request.path}?conversation={active_conversation.id}")
        except User.DoesNotExist:
            pass # Gérer l'erreur si le destinataire n'existe pas

    # Vérifier si une conversation existante est demandée
    conversation_id = request.GET.get('conversation')
    if conversation_id:
        try:
            active_conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
            messages = active_conversation.messages.all().order_by('created_at')
            # Marquer les messages comme lus
            active_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        except Conversation.DoesNotExist:
            # Gérer le cas où l'ID de conversation n'est pas valide ou n'appartient pas à l'utilisateur
            pass
    
    # Gérer l'envoi d'un nouveau message
    if request.method == 'POST' and active_conversation:
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=active_conversation,
                sender=request.user,
                content=content
            )
            return redirect(f"{request.path}?conversation={active_conversation.id}")

    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
    }
    return render(request, 'messaging/messages.html', context)

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les conversations
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les conversations de l'utilisateur connecté"""
        user = self.request.user

        # Sous-requête pour trouver le contenu du dernier message
        last_message_content = Message.objects.filter(
            conversation=OuterRef('pk')
        ).order_by('-created_at').values('content')[:1]

        # Sous-requête pour trouver la date du dernier message
        last_message_date = Message.objects.filter(
            conversation=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]
        
        # Compter les messages non lus pour chaque conversation
        unread_count = Message.objects.filter(
            conversation=OuterRef('pk'), is_read=False
        ).exclude(sender=user).values('conversation').annotate(count=Count('id')).values('count')

        return Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants').annotate(
            last_message_content=Subquery(last_message_content),
            last_message_date=Subquery(last_message_date),
            unread_count=Subquery(unread_count, output_field=models.IntegerField())
        ).order_by(F('last_message_date').desc(nulls_last=True))
    
    def create(self, request, *args, **kwargs):
        """Créer une nouvelle conversation"""
        serializer = ConversationCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        # Renvoyer une réponse simple avec l'ID de la conversation pour que le JavaScript puisse facilement le récupérer.
        return Response(
            {'id': conversation.id}, status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Récupérer tous les messages d'une conversation"""
        conversation = self.get_object()
        messages = conversation.messages.all()
        
        # Marquer les messages comme lus
        messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Envoyer un message dans une conversation"""
        conversation = self.get_object()
        
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                conversation=conversation,
                sender=request.user
            )
            
            # Mettre à jour la date de modification de la conversation
            conversation.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtenir le nombre total de messages non lus"""
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return Response({'unread_count': count})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les messages des conversations de l'utilisateur"""
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('sender', 'conversation')
    
    def perform_create(self, serializer):
        """Créer un nouveau message"""
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marquer un message comme lu"""
        message = self.get_object()
        
        if message.sender != request.user:
            message.mark_as_read()
            return Response({'status': 'message marked as read'})
        
        return Response(
            {'error': 'Cannot mark own message as read'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def mark_conversation_read(self, request):
        """Marquer tous les messages d'une conversation comme lus"""
        conversation_id = request.data.get('conversation_id')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return Response({'status': 'all messages marked as read'})