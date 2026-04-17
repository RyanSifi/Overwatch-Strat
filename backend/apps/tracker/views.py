"""
Views pour le tracker de parties.
Tous les endpoints requièrent une authentification.
"""
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.heroes.models import Hero
from .models import GameSession
from .serializers import GameSessionReadSerializer, GameSessionWriteSerializer


class GameSessionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/tracker/sessions/  → historique paginé de l'utilisateur
    POST /api/tracker/sessions/  → enregistre une nouvelle partie
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GameSessionWriteSerializer
        return GameSessionReadSerializer

    def get_queryset(self):
        return GameSession.objects.filter(user=self.request.user).select_related(
            "hero_played", "map_played"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GameSessionDeleteView(generics.DestroyAPIView):
    """DELETE /api/tracker/sessions/<id>/"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # L'utilisateur ne peut supprimer que ses propres sessions
        return GameSession.objects.filter(user=self.request.user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tracker_stats(request):
    """
    GET /api/tracker/stats/
    Calcule les statistiques de l'utilisateur :
    - win_rate global
    - win_rate par héros (min 3 parties)
    - win_rate par map
    - win_rate par rôle
    - évolution hebdomadaire sur 30 jours
    """
    sessions = GameSession.objects.filter(user=request.user)
    total    = sessions.count()

    if total == 0:
        return Response({
            "total_games":    0,
            "win_rate_global": 0,
            "by_hero":        [],
            "by_map":         [],
            "by_role":        [],
            "weekly_progress": [],
        })

    def _win_rate(wins, played):
        return round((wins / played) * 100, 1) if played > 0 else 0

    # ── Win rate global ──────────────────────────────────────────────────────
    wins_global  = sessions.filter(result="win").count()
    wr_global    = _win_rate(wins_global, total)

    # ── Win rate par héros (min 3 parties) ───────────────────────────────────
    by_hero = []
    hero_ids = sessions.exclude(hero_played=None).values_list("hero_played_id", flat=True).distinct()
    for hero_id in hero_ids:
        hero_sessions = sessions.filter(hero_played_id=hero_id)
        played = hero_sessions.count()
        if played < 3:
            continue
        wins = hero_sessions.filter(result="win").count()
        try:
            hero = Hero.objects.get(pk=hero_id)
            by_hero.append({
                "slug":     hero.slug,
                "name":     hero.name,
                "role":     hero.role,
                "icon_url": hero.icon_url,
                "played":   played,
                "wins":     wins,
                "win_rate": _win_rate(wins, played),
            })
        except Hero.DoesNotExist:
            continue
    by_hero.sort(key=lambda x: x["win_rate"], reverse=True)

    # ── Win rate par map ─────────────────────────────────────────────────────
    by_map = []
    map_ids = sessions.exclude(map_played=None).values_list("map_played_id", flat=True).distinct()
    for map_id in map_ids:
        map_sessions = sessions.filter(map_played_id=map_id)
        played = map_sessions.count()
        wins   = map_sessions.filter(result="win").count()
        try:
            from apps.heroes.models import Map
            m = Map.objects.get(pk=map_id)
            by_map.append({
                "slug":     m.slug,
                "name":     m.name,
                "map_type": m.map_type,
                "played":   played,
                "wins":     wins,
                "win_rate": _win_rate(wins, played),
            })
        except Exception:
            continue
    by_map.sort(key=lambda x: x["win_rate"], reverse=True)

    # ── Win rate par rôle (basé sur le héros joué) ───────────────────────────
    by_role = []
    for role in ["tank", "dps", "support"]:
        role_sessions = sessions.filter(hero_played__role=role)
        played = role_sessions.count()
        if played == 0:
            continue
        wins = role_sessions.filter(result="win").count()
        by_role.append({
            "role":     role,
            "played":   played,
            "wins":     wins,
            "win_rate": _win_rate(wins, played),
        })

    # ── Évolution hebdomadaire sur 30 jours ──────────────────────────────────
    now        = timezone.now()
    start_date = now - timedelta(days=30)
    weekly_progress = []

    for week in range(4):
        week_end   = now - timedelta(weeks=week)
        week_start = week_end - timedelta(weeks=1)
        week_sessions = sessions.filter(played_at__gte=week_start, played_at__lt=week_end)
        played = week_sessions.count()
        wins   = week_sessions.filter(result="win").count()
        weekly_progress.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end":   week_end.strftime("%Y-%m-%d"),
            "played":     played,
            "wins":       wins,
            "win_rate":   _win_rate(wins, played),
        })

    weekly_progress.reverse()  # Du plus ancien au plus récent

    return Response({
        "total_games":     total,
        "win_rate_global": wr_global,
        "by_hero":         by_hero,
        "by_map":          by_map,
        "by_role":         by_role,
        "weekly_progress": weekly_progress,
    })
