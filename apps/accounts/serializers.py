from rest_framework import serializers
from .models import User, PhoneOTP, UserLocation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'display_name', 'avatar', 'is_phone_verified', 'date_joined']
        read_only_fields = ['id', 'is_phone_verified', 'date_joined']


class UserRegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    display_name = serializers.CharField(max_length=100)
    
    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered")
        return value


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=17)
    otp = serializers.CharField(max_length=6)


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['id', 'latitude', 'longitude', 'city', 'country', 'updated_at', 'is_current']
        read_only_fields = ['id', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'display_name', 'avatar', 'is_phone_verified', 'current_location', 'date_joined']
        read_only_fields = ['id', 'phone_number', 'is_phone_verified', 'date_joined']
    
    def get_current_location(self, obj):
        location = obj.locations.filter(is_current=True).first()
        if location:
            return UserLocationSerializer(location).data
        return None