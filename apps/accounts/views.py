from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, UserLocationSerializer, UserProfileSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Crée un nouvel utilisateur ou récupère un utilisateur existant par numéro de téléphone.
    Marque immédiatement l'utilisateur comme vérifié et retourne les tokens JWT pour la connexion.
    Ceci contourne la vérification OTP pour le développement et les tests.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        display_name = request.data.get('display_name')

        if not phone_number or not display_name:
            return Response(
                {'error': 'Phone number and display name are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crée ou récupère l'utilisateur
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'display_name': display_name}
        )

        # Met à jour le nom d'affichage si l'utilisateur existait déjà
        if not created:
            user.display_name = display_name

        # Marque l'utilisateur comme vérifié
        user.is_phone_verified = True
        user.is_active = True
        user.save()

        # Génère les tokens JWT
        refresh = RefreshToken.for_user(user)

        # Sérialise les données de l'utilisateur
        user_data = self.get_serializer(user).data

        return Response({
            'message': 'User registered and logged in successfully.',
            'user': user_data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    """
    Connecte un utilisateur existant via son numéro de téléphone et retourne les tokens JWT.
    Ceci contourne la vérification OTP.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response(
                {'error': 'Phone number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this phone number does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Génère les tokens JWT
        refresh = RefreshToken.for_user(user)
        user_data = self.get_serializer(user).data

        return Response({
            'message': 'User logged in successfully.',
            'user': user_data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserLocationView(generics.CreateAPIView):
    """Update user's current location"""
    serializer_class = UserLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_current=True)