"""
Vues d'authentification pour les pages web
"""
from django.shortcuts import render, redirect
from django.contrib import messages

def register(request):
    """Page d'inscription"""
    return render(request, 'auth/register.html')

def verify_otp(request):
    """Page de vérification OTP"""
    return render(request, 'auth/verify_otp.html')

def login_view(request):
    """Page de connexion"""
    return render(request, 'auth/login.html')

def logout_view(request):
    """Déconnexion"""
    # La déconnexion est gérée côté frontend (suppression du frontend)
    messages.success(request, 'Vous avez été déconnecté avec succès')
    return redirect('home')