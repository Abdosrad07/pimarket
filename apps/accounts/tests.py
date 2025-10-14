﻿import pytest
from rest_framework.test import APIClient
from rest_framework import status

from .models import User, PhoneOTP

# Marqueur pour indiquer que ces tests nécessitent un accès à la base de données
pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    """Fixture pour créer un client API pour les tests."""
    return APIClient()


class TestAuthentication:
    """Suite de tests pour le flux d'authentification."""

    def test_register_and_login_new_user(self, api_client):
        """
        Vérifie que l'inscription d'un nouvel utilisateur fonctionne,
        le connecte et retourne des tokens JWT.
        """
        phone_number = "+221771234567"
        display_name = "Test User"
        
        assert User.objects.filter(phone_number=phone_number).count() == 0

        response = api_client.post('/api/accounts/register/', {
            'phone_number': phone_number,
            'display_name': display_name
        })

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data['message'] == "User registered and logged in successfully."
        assert 'access' in response.data
        assert 'refresh' in response.data
        
        # Vérifier que l'utilisateur a été créé et est vérifié
        user = User.objects.get(phone_number=phone_number)
        assert user is not None
        assert user.is_phone_verified

    def test_register_missing_fields(self, api_client):
        """Vérifie que les champs requis sont validés."""
        response = api_client.post('/api/accounts/register/', {'phone_number': '+221771234569'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data, response.data