"""
Serializers pour Hero et Map.
"""
from rest_framework import serializers
from .models import Hero, Map


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hero
        fields = [
            "id", "name", "slug", "role", "subrole",
            "tier", "styles", "counters", "is_new", "icon_url",
        ]


class HeroListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes (sans counters)."""
    class Meta:
        model = Hero
        fields = ["id", "name", "slug", "role", "subrole", "tier", "styles", "traits", "is_new", "icon_url"]


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ["id", "name", "slug", "map_type", "phases"]
