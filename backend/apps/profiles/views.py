"""
Views pour le profil joueur et la synchronisation OverFast API.
"""
import requests

from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import PlayerProfile
from .serializers import PlayerProfileSerializer

OVERFAST_BASE_URL = "https://overfast-api.tekrop.fr"
CACHE_TTL = 60 * 60  # 1 heure


def _get_or_create_profile(user):
    """Récupère ou crée le profil OW de l'utilisateur."""
    profile, _ = PlayerProfile.objects.get_or_create(user=user)
    return profile


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_me(request):
    """
    GET   /api/profiles/me/   → retourne le profil complet
    PATCH /api/profiles/me/   → met à jour le battletag (et autres champs)
    """
    profile = _get_or_create_profile(request.user)

    if request.method == "GET":
        return Response(PlayerProfileSerializer(profile).data)

    # PATCH
    serializer = PlayerProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def profile_sync(request):
    """
    POST /api/profiles/sync/
    Synchronise les stats depuis OverFast API.
    Met en cache Redis pendant 1 heure pour éviter de surcharger l'API.

    OverFast retourne :
    {
      "username": "...",
      "competitive": {
        "pc": {
          "season": {
            "tank":    { "division": "gold",     "tier": 3 },
            "damage":  { "division": "platinum",  "tier": 2 },
            "support": { "division": "diamond",   "tier": 1 }
          }
        }
      },
      "most_played_heroes": { "pc": { "quickplay": [...], "competitive": [...] } }
    }
    """
    profile = _get_or_create_profile(request.user)

    if not profile.battletag:
        return Response(
            {"error": "Aucun BattleTag renseigné. Configure-le d'abord via PATCH /api/profiles/me/"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Vérifie le cache Redis (évite les appels répétés)
    cache_key   = f"overfast_profile_{profile.battletag}"
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response({
            "message": "Données récupérées depuis le cache (moins d'1 heure).",
            "profile": PlayerProfileSerializer(profile).data,
            "cached":  True,
        })

    # Appel OverFast API
    # Le BattleTag doit être au format "Pseudo-12345" (tiret, pas dièse) pour l'URL
    battletag_url = profile.battletag.replace("#", "-")
    url = f"{OVERFAST_BASE_URL}/players/{battletag_url}/summary"

    try:
        response = requests.get(url, timeout=10)
    except requests.Timeout:
        return Response(
            {"error": "OverFast API timeout. Réessaie dans quelques instants."},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except requests.RequestException as e:
        return Response(
            {"error": f"Impossible de contacter OverFast API : {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if response.status_code == 404:
        return Response(
            {"error": f"Joueur '{profile.battletag}' introuvable sur OverFast. Vérifie ton BattleTag."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if response.status_code != 200:
        return Response(
            {"error": f"OverFast API a retourné une erreur ({response.status_code})."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    data = response.json()

    # ── Extraction des rangs compétitifs ─────────────────────────────────────
    try:
        season = data.get("competitive", {}).get("pc", {}).get("season", {})
        def _format_rank(role_data):
            if not role_data:
                return ""
            division = role_data.get("division", "").capitalize()
            tier     = role_data.get("tier", "")
            return f"{division} {tier}".strip() if division else ""

        profile.rank_tank    = _format_rank(season.get("tank"))
        profile.rank_dps     = _format_rank(season.get("damage"))
        profile.rank_support = _format_rank(season.get("support"))
    except Exception:
        pass  # Les rangs restent vides si la structure est inattendue

    # ── Extraction des héros les plus joués ──────────────────────────────────
    try:
        most_played_data = (
            data.get("most_played_heroes", {})
                .get("pc", {})
                .get("competitive", [])
        )
        # Prend les 5 premiers slugs
        profile.most_played = [
            hero["slug"] for hero in most_played_data[:5]
            if isinstance(hero, dict) and "slug" in hero
        ]
    except Exception:
        pass

    profile.last_synced = timezone.now()
    profile.save()

    # Met en cache pour 1 heure
    cache.set(cache_key, True, CACHE_TTL)

    return Response({
        "message": "Profil synchronisé avec succès.",
        "profile": PlayerProfileSerializer(profile).data,
        "cached":  False,
    })
