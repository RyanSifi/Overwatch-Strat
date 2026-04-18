"""
Serializers pour Hero et Map.
"""
from rest_framework import serializers
from .models import Hero, Map, MetaComp, PatchNote


class HeroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hero
        fields = [
            "id", "name", "slug", "role", "subrole",
            "tier", "styles", "counters", "synergies", "traits", "is_new", "icon_url", "difficulty",
        ]


class HeroListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes (sans counters/synergies)."""
    class Meta:
        model = Hero
        fields = ["id", "name", "slug", "role", "subrole", "tier", "styles", "traits", "is_new", "icon_url", "difficulty"]


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ["id", "name", "slug", "map_type", "phases"]


class PatchNoteSerializer(serializers.ModelSerializer):
    changes_enriched = serializers.SerializerMethodField()

    class Meta:
        model  = PatchNote
        fields = ["id", "version", "date", "title", "summary", "changes", "changes_enriched", "is_latest"]

    def get_changes_enriched(self, obj):
        result = []
        for change in obj.changes:
            slug = change.get("hero_slug")
            hero_data = {"slug": slug, "name": slug, "role": None, "icon_url": ""}
            if slug:
                try:
                    h = Hero.objects.get(slug=slug)
                    hero_data = {"slug": h.slug, "name": h.name, "role": h.role, "icon_url": h.icon_url}
                except Hero.DoesNotExist:
                    pass
            result.append({**change, "hero": hero_data})
        return result


class MetaCompSerializer(serializers.ModelSerializer):
    """Comp méta enrichie avec les données complètes de chaque héros."""
    heroes_data = serializers.SerializerMethodField()

    class Meta:
        model  = MetaComp
        fields = ["id", "name", "style", "tier", "description", "heroes", "heroes_data", "patch", "win_rate", "is_featured"]

    def get_heroes_data(self, obj):
        result = []
        for slug in obj.heroes:
            try:
                h = Hero.objects.get(slug=slug)
                result.append({"slug": h.slug, "name": h.name, "role": h.role, "tier": h.tier, "icon_url": h.icon_url})
            except Hero.DoesNotExist:
                result.append({"slug": slug, "name": slug, "role": None, "tier": None, "icon_url": ""})
        return result
