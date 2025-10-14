import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from .serializers import MessageSerializer

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour la messagerie en temps réel
    """
    
    async def connect(self):
        """Connexion WebSocket"""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Vérifier si l'utilisateur est authentifié
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Vérifier si l'utilisateur fait partie de la conversation
        is_participant = await self.is_conversation_participant()
        if not is_participant:
            await self.close()
            return
        
        # Rejoindre le groupe de la conversation
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer un message de confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté à la conversation'
        }))
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        # Quitter le groupe de la conversation
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                content = data.get('message')
                
                if not content or not content.strip():
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Le message ne peut pas être vide'
                    }))
                    return
                
                # Sauvegarder le message dans la base de données
                message = await self.save_message(content)
                
                if message:
                    # Diffuser le message à tous les participants
                    await self.channel_layer.group_send(
                        self.conversation_group_name,
                        {
                            'type': 'chat_message',
                            'message': message
                        }
                    )
            
            elif message_type == 'typing':
                # Diffuser l'indicateur de frappe
                is_typing = data.get('is_typing', False)
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )
            
            elif message_type == 'mark_read':
                # Marquer les messages comme lus
                await self.mark_messages_read()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Format JSON invalide'
            }))
    
    async def chat_message(self, event):
        """Recevoir un message du groupe et l'envoyer au WebSocket"""
        message = event['message']
        
        # Envoyer le message au WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        """Envoyer l'indicateur de frappe"""
        # Ne pas envoyer l'indicateur à l'utilisateur qui tape
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def is_conversation_participant(self):
        """Vérifier si l'utilisateur fait partie de la conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Sauvegarder le message dans la base de données"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            
            # Sérialiser le message
            serializer = MessageSerializer(message)
            return serializer.data
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du message: {e}")
            return None
    
    @database_sync_to_async
    def mark_messages_read(self):
        """Marquer tous les messages de la conversation comme lus"""
        try:
            Message.objects.filter(
                conversation_id=self.conversation_id,
                is_read=False
            ).exclude(sender=self.user).update(is_read=True)
        except Exception as e:
            print(f"Erreur lors du marquage des messages: {e}")

User = get_user_model()