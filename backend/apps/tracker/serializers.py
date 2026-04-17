"""
Serializers pour GameSession.
"""
from rest_framework import serializers
from .models import GameSession
from apps.heroes.serializers import HeroListSerializer, MapSerializer


class GameSessionWriteSerializer(serializers.ModelSerializer):
    """Utilisé en écriture : hero_played et map_played reçus comme slugs."""
    hero_slug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=__import__("apps.heroes.models", fromlist=["Hero"]).Hero.objects.all(),
        source="hero_played",
        required=False,
        allow_null=True,
    )
    map_slug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=__import__("apps.heroes.models", fromlist=["Map"]).Map.objects.all(),
        source="map_played",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = GameSession
        fields = ["id", "hero_slug", "map_slug", "result", "ally_comp", "enemy_comp", "notes", "played_at"]
        read_only_fields = ["id", "played_at"]


class GameSessionReadSerializer(serializers.ModelSerializer):
    """Utilisé en lecture : retourne les objets complets."""
    hero_played = HeroListSerializer(read_only=True)
    map_played  = MapSerializer(read_only=True)

    class Meta:
        model = GameSession
        fields = ["id", "hero_played", "map_played", "result", "ally_comp", "enemy_comp", "notes", "played_at"]
