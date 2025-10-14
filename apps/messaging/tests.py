import pytest
import json
import random
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

from pimarket.asgi import application  # Assurez-vous que le chemin est correct
from .models import Conversation

User = get_user_model()

# Marqueurs pour les tests de base de données et asynchrones
pytestmark = [pytest.mark.django_db, pytest.mark.asyncio]


@pytest.fixture
async def test_users():
    """Fixture pour créer deux utilisateurs de test."""
    # Utiliser des numéros aléatoires pour éviter les conflits de clés uniques
    rand_suffix1 = random.randint(10000, 99999)
    rand_suffix2 = random.randint(10000, 99999)
    user1 = await User.objects.acreate(username='user1', phone_number=f'+111{rand_suffix1}')
    user2 = await User.objects.acreate(username='user2', phone_number=f'+222{rand_suffix2}')
    return user1, user2


@pytest.fixture
async def test_conversation(test_users):
    """Fixture pour créer une conversation entre les deux utilisateurs."""
    user1, user2 = await test_users
    conversation = await Conversation.objects.acreate()
    await conversation.participants.aadd(user1, user2)
    return conversation


class TestChatConsumer:
    """Suite de tests pour le ChatConsumer."""

    async def test_user_can_connect_and_send_message(self, test_conversation):
        """
        Vérifie qu'un participant peut se connecter, envoyer un message,
        et que l'autre participant le reçoit.
        """
        conversation = await test_conversation
        conversation_id = conversation.id
        user1, user2 = await database_sync_to_async(list)(conversation.participants.all())

        # Communicator pour le premier utilisateur
        communicator1 = WebsocketCommunicator(application, f"/ws/chat/{conversation_id}/")
        communicator1.scope['user'] = user1
        connected1, _ = await communicator1.connect()
        assert connected1, "L'utilisateur 1 n'a pas pu se connecter."

        # Communicator pour le second utilisateur
        communicator2 = WebsocketCommunicator(application, f"/ws/chat/{conversation_id}/")
        communicator2.scope['user'] = user2
        connected2, _ = await communicator2.connect()
        assert connected2, "L'utilisateur 2 n'a pas pu se connecter."

        # L'utilisateur 1 envoie un message
        test_message = "Bonjour, monde !"
        await communicator1.send_to(text_data=json.dumps({
            'type': 'chat_message',
            'message': test_message
        }))

        # L'utilisateur 2 doit recevoir le message
        response2 = await communicator2.receive_from()
        data2 = json.loads(response2)
        assert data2['type'] == 'chat_message'
        assert data2['message']['content'] == test_message
        assert data2['message']['sender']['username'] == user1.username

        # L'utilisateur 1 doit aussi recevoir son propre message
        response1 = await communicator1.receive_from()
        data1 = json.loads(response1)
        assert data1['type'] == 'chat_message'
        assert data1['message']['content'] == test_message

        # Fermer les connexions
        await communicator1.disconnect()
        await communicator2.disconnect()