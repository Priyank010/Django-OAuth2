# your_app/urls.py

from django.urls import path
from .views import UserRegistrationView, CheckUserExistsView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('check-user/', CheckUserExistsView.as_view(), name='check-user'),
    # ... other API endpoints
]
