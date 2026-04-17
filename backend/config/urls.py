"""
URLs racines de l'application OW Coach.
Toutes les routes API sont préfixées /api/.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email    = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/auth/register/
    Crée un compte et retourne le token d'authentification.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data["username"]
    email    = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    if User.objects.filter(username=username).exists():
        return Response({"error": "Ce nom d'utilisateur est déjà pris."}, status=status.HTTP_409_CONFLICT)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Cet email est déjà utilisé."}, status=status.HTTP_409_CONFLICT)

    user  = User.objects.create_user(username=username, email=email, password=password)
    token = Token.objects.create(user=user)

    return Response({
        "token":    token.key,
        "user_id":  user.pk,
        "username": user.username,
        "email":    user.email,
    }, status=status.HTTP_201_CREATED)


urlpatterns = [
    path("admin/", admin.site.urls),

    # Apps OW Coach
    path("api/", include("apps.heroes.urls")),
    path("api/", include("apps.tracker.urls")),
    path("api/", include("apps.coach.urls")),
    path("api/", include("apps.profiles.urls")),

    # Auth : POST /api/auth/login/  → { token, user_id, ... }
    #        POST /api/auth/register/ → idem
    path("api/auth/login/",    obtain_auth_token, name="auth-login"),
    path("api/auth/register/", register,          name="auth-register"),
]
