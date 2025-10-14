from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, UserLocationView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('update-location/', UserLocationView.as_view(), name='update-location'),
]