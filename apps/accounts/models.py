from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import random
import string

from .managers import UserManager

class User(AbstractUser):
    """Custom User model with phone authentication"""
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        db_index=True
    )
    is_phone_verified = models.BooleanField(default=False)
    display_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Override username to make it optional
    username = models.CharField(max_length=150, blank=True, null=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['display_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.display_name} ({self.phone_number})"


class PhoneOTP(models.Model):
    """OTP model for phone verification"""
    phone_number = models.CharField(max_length=17, db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Phone OTP'
        verbose_name_plural = 'Phone OTPs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.phone_number}"
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at
    
    def verify(self, otp_input):
        """Verify OTP with attempt tracking"""
        self.attempts += 1
        self.save()
        
        if self.attempts > 5:
            return False, "Too many attempts"
        
        if self.is_expired():
            return False, "OTP expired"
        
        if self.otp == otp_input:
            self.is_verified = True
            self.save()
            return True, "OTP verified"
        
        return False, "Invalid OTP"


class UserLocation(models.Model):
    """Store user's geolocation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_current = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Location'
        verbose_name_plural = 'User Locations'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.display_name} - {self.latitude},{self.longitude}"
    
    def save(self, *args, **kwargs):
        """Set other locations to not current when saving a new current location"""
        if self.is_current:
            UserLocation.objects.filter(user=self.user, is_current=True).update(is_current=False)
        super().save(*args, **kwargs)