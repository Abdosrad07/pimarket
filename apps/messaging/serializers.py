from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les informations utilisateur"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User 
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class MessageSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les messages"""
    sender = UserSerializer(read_only=True)
    time_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'is_read', 
                  'created_at', 'time_display', 'attachment']
        read_only_fields = ['sender', 'created_at']
    
    def get_time_display(self, obj):
        """Formate l'heure d'affichage"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days == 0:
            return obj.created_at.strftime('%H:%M')
        elif diff.days == 1:
            return 'Hier'
        elif diff.days < 7:
            return obj.created_at.strftime('%A')
        else:
            return obj.created_at.strftime('%d/%m/%Y')


class ConversationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les conversations"""
    participants = UserSerializer(many=True, read_only=True)
    # Utiliser directement les champs annotés par la vue
    last_message_content = serializers.CharField(read_only=True)
    last_message_date = serializers.DateTimeField(read_only=True)
    unread_count = serializers.IntegerField(read_only=True, default=0)
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'last_message_content', 'last_message_date', 
                  'unread_count', 'other_participant', 'product']
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            if other:
                return UserSerializer(other).data
        return None


class ConversationCreateSerializer(serializers.Serializer):
    """Sérialiseur pour créer une conversation"""
    recipient_id = serializers.IntegerField()
    product_id = serializers.IntegerField(required=False, allow_null=True)
    initial_message = serializers.CharField(required=False, allow_blank=True)
    
    def validate_recipient_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("L'utilisateur destinataire n'existe pas.")
        return value
    
    def create(self, validated_data):
        request = self.context['request']
        sender = request.user
        recipient_id = validated_data['recipient_id']
        recipient = User.objects.get(id=recipient_id)
        
        # Vérifier si une conversation existe déjà
        existing = Conversation.objects.filter(
            participants=sender
        ).filter(
            participants=recipient
        ).first()
        
        if existing:
            conversation = existing
        else:
            conversation = Conversation.objects.create()
            conversation.participants.add(sender, recipient)
        
        # Ajouter un message initial si fourni
        initial_message = validated_data.get('initial_message')
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=initial_message
            )
        
        # Lier à un produit si spécifié
        product_id = validated_data.get('product_id')
        if product_id:
            from apps.shops.models import Product
            try:
                product = Product.objects.get(id=product_id)
                conversation.product = product
                conversation.save()
            except Product.DoesNotExist:
                pass
        
        return conversation