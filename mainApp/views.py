# your_app/views.py

from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, UserExistenceSerializer
from oauth2_provider.models import Application
from oauthlib.common import generate_token
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Automatically generate a token for the user
        self.create_token(user)

    def create_token(self, user):
        # Get the OAuth2 application
        try:
            application = Application.objects.get(name='AppTest')  # Replace with your app name
        except Application.DoesNotExist:
            raise Exception("OAuth2 Application not found. Please create one in the admin panel.")

        # Create a token
        token = generate_token()
        # Normally, tokens are created via the OAuth2 flow. For simplicity, you might want to redirect the user to obtain a token via the token endpoint.
        # Alternatively, use django-oauth-toolkit's models to create tokens programmatically.
        # Here's an example using AccessToken:

        from oauth2_provider.models import AccessToken
        from datetime import timedelta
        from django.utils import timezone

        access_token = AccessToken.objects.create(
            user=user,
            scope='read write',
            expires=timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']),
            token=generate_token(),
            application=application
        )
        return access_token

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        token = self.create_token(user)
        response.data['token'] = token.token
        return response

class CheckUserExistsView(generics.GenericAPIView):
    serializer_class = UserExistenceSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
            # Generate or retrieve existing token
            token = self.get_or_create_token(user)
            return Response({'exists': True, 'token': token.token}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'exists': False}, status=status.HTTP_404_NOT_FOUND)

    def get_or_create_token(self, user):
        # Retrieve existing valid token or create a new one
        from oauth2_provider.models import AccessToken
        from datetime import timedelta
        from django.utils import timezone
        from oauthlib.common import generate_token

        # Get the OAuth2 application
        try:
            application = Application.objects.get(name='AppTest')  # Replace with your app name
        except Application.DoesNotExist:
            raise Exception("OAuth2 Application not found. Please create one in the admin panel.")

        # Check for existing valid token
        token = AccessToken.objects.filter(user=user, application=application, expires__gt=timezone.now()).first()
        if token:
            return token
        else:
            # Create a new token
            token = AccessToken.objects.create(
                user=user,
                scope='read write',
                expires=timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']),
                token=generate_token(),
                application=application
            )
            return token

from rest_framework import viewsets, permissions
from .models import Item
from .serializers import ItemSerializer

class ItemViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard CRUD actions for Item.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Assign the item to the authenticated user
        serializer.save(owner=self.request.user)