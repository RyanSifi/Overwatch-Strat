"""
Views pour les héros, maps et counter-picker.
Tous les endpoints publics (aucune authentification requise).
"""
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Hero, Map
from .serializers import HeroSerializer, HeroListSerializer, MapSerializer


# ─── Héros ───────────────────────────────────────────────────────────────────

class HeroListView(generics.ListAPIView):
    """
    GET /api/heroes/
    Retourne tous les héros. Supporte les filtres :
    ?role=tank|dps|support
    ?tier=S|A|B|C|D
    ?style=brawl|dive|poke
    ?is_new=true
    """
    permission_classes = [AllowAny]
    serializer_class   = HeroListSerializer

    def get_queryset(self):
        qs = Hero.objects.all()
        role   = self.request.query_params.get("role")
        tier   = self.request.query_params.get("tier")
        style  = self.request.query_params.get("style")
        is_new = self.request.query_params.get("is_new")

        if role:
            qs = qs.filter(role=role)
        if tier:
            qs = qs.filter(tier=tier)
        if style:
            # JSONField contains : filtre les héros dont styles contient la valeur
            qs = qs.filter(styles__contains=[style])
        if is_new and is_new.lower() == "true":
            qs = qs.filter(is_new=True)
        return qs


class HeroDetailView(generics.RetrieveAPIView):
    """GET /api/heroes/<slug>/"""
    permission_classes = [AllowAny]
    serializer_class   = HeroSerializer
    queryset           = Hero.objects.all()
    lookup_field       = "slug"


@api_view(["GET"])
@permission_classes([AllowAny])
def hero_counters(request, slug):
    """
    GET /api/heroes/<slug>/counters/
    Retourne les counters d'un héros avec le détail de chaque héros counter.
    Sépare en deux listes : favorable (score > 0) et défavorable (score < 0).
    """
    try:
        hero = Hero.objects.get(slug=slug)
    except Hero.DoesNotExist:
        return Response({"error": f"Héros '{slug}' introuvable."}, status=status.HTTP_404_NOT_FOUND)

    favorable   = {}
    defavorable = {}

    for enemy_slug, score in hero.counters.items():
        try:
            enemy = Hero.objects.get(slug=enemy_slug)
            data  = {
                "slug":    enemy.slug,
                "name":    enemy.name,
                "role":    enemy.role,
                "tier":    enemy.tier,
                "icon_url": enemy.icon_url,
                "score":   score,
            }
            if score > 0:
                favorable[enemy_slug] = data
            else:
                defavorable[enemy_slug] = data
        except Hero.DoesNotExist:
            # Ignore les slugs obsolètes dans les fixtures
            continue

    # Trie par score décroissant / croissant
    favorable_sorted   = sorted(favorable.values(),   key=lambda x: x["score"], reverse=True)
    defavorable_sorted = sorted(defavorable.values(), key=lambda x: x["score"])

    return Response({
        "hero":       HeroSerializer(hero).data,
        "favorable":  favorable_sorted,
        "defavorable": defavorable_sorted,
    })


# ─── Maps ────────────────────────────────────────────────────────────────────

class MapListView(generics.ListAPIView):
    """
    GET /api/maps/
    Retourne toutes les maps. Filtre optionnel : ?map_type=escort|control|hybrid|push|flashpoint
    """
    permission_classes = [AllowAny]
    serializer_class   = MapSerializer

    def get_queryset(self):
        qs       = Map.objects.all()
        map_type = self.request.query_params.get("map_type")
        if map_type:
            qs = qs.filter(map_type=map_type)
        return qs


@api_view(["GET"])
@permission_classes([AllowAny])
def map_guide(request, slug):
    """
    GET /api/maps/<slug>/guide/
    Retourne le guide complet d'une map : chaque phase avec style, notes
    et les héros recommandés enrichis (tier, subrole, etc.).
    """
    try:
        map_obj = Map.objects.get(slug=slug)
    except Map.DoesNotExist:
        return Response({"error": f"Map '{slug}' introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # Enrichit les picks recommandés avec les données complètes des héros
    enriched_phases = []
    for phase in map_obj.phases:
        enriched_recommended = {}
        for role, slugs in phase.get("recommended", {}).items():
            heroes_data = []
            for hero_slug in slugs:
                try:
                    h = Hero.objects.get(slug=hero_slug)
                    heroes_data.append({
                        "slug":     h.slug,
                        "name":     h.name,
                        "tier":     h.tier,
                        "subrole":  h.subrole,
                        "icon_url": h.icon_url,
                    })
                except Hero.DoesNotExist:
                    heroes_data.append({"slug": hero_slug, "name": hero_slug})
            enriched_recommended[role] = heroes_data

        enriched_phases.append({
            "name":        phase.get("name"),
            "style":       phase.get("style"),
            "notes":       phase.get("notes", ""),
            "recommended": enriched_recommended,
        })

    return Response({
        "map":    MapSerializer(map_obj).data,
        "phases": enriched_phases,
    })


# ─── Counter-picker ───────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def suggest_counters(request):
    """
    POST /api/counters/suggest/
    Body : { "enemy_heroes": ["domina", "sojourn", "ana"] }

    Algorithme :
    1. Pour chaque héros de la liste ennemie, parcourt TOUS les héros de la BDD.
    2. Si un héros a un score positif contre cet ennemi dans son dict 'counters',
       on ajoute ce score à son score total.
    3. On déduplique et trie par score décroissant.
    4. On retourne les 3 meilleurs par rôle avec explication.
    """
    enemy_slugs = request.data.get("enemy_heroes", [])
    if not enemy_slugs:
        return Response({"error": "Champ 'enemy_heroes' requis."}, status=status.HTTP_400_BAD_REQUEST)
    if len(enemy_slugs) > 6:
        return Response({"error": "Maximum 6 héros ennemis."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie que les slugs ennemis existent
    valid_enemy_slugs = []
    for slug in enemy_slugs:
        if Hero.objects.filter(slug=slug).exists():
            valid_enemy_slugs.append(slug)

    if not valid_enemy_slugs:
        return Response({"error": "Aucun héros ennemi valide."}, status=status.HTTP_400_BAD_REQUEST)

    # Calcul des scores agrégés
    # score_map : { hero_slug: { total_score, covered_enemies: [], hero_obj } }
    score_map = {}

    all_heroes = Hero.objects.all()
    for hero in all_heroes:
        # Ignore les héros ennemis eux-mêmes dans les suggestions
        if hero.slug in valid_enemy_slugs:
            continue

        total_score    = 0
        covered        = []

        for enemy_slug in valid_enemy_slugs:
            score = hero.counters.get(enemy_slug, 0)
            if score > 0:
                total_score += score
                covered.append(enemy_slug)

        if total_score > 0:
            score_map[hero.slug] = {
                "hero":           hero,
                "total_score":    total_score,
                "covered_enemies": covered,
            }

    # Trie par score décroissant et regroupe par rôle
    sorted_heroes = sorted(score_map.values(), key=lambda x: x["total_score"], reverse=True)

    result = {"tank": [], "dps": [], "support": []}

    for entry in sorted_heroes:
        hero  = entry["hero"]
        role  = hero.role
        if role not in result:
            continue
        if len(result[role]) >= 3:
            continue

        # Génère une explication lisible
        if entry["covered_enemies"]:
            covered_names = []
            for s in entry["covered_enemies"]:
                try:
                    covered_names.append(Hero.objects.get(slug=s).name)
                except Hero.DoesNotExist:
                    covered_names.append(s)
            reason = f"Bon contre {', '.join(covered_names)} (score {entry['total_score']})"
        else:
            reason = "Polyvalent dans cette composition"

        result[role].append({
            "slug":            hero.slug,
            "name":            hero.name,
            "role":            hero.role,
            "subrole":         hero.subrole,
            "tier":            hero.tier,
            "styles":          hero.styles,
            "icon_url":        hero.icon_url,
            "total_score":     entry["total_score"],
            "covered_enemies": entry["covered_enemies"],
            "reason":          reason,
        })

    return Response({
        "enemy_heroes": valid_enemy_slugs,
        "suggestions":  result,
    })
