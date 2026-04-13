"""
Modèle pour l'historique des parties jouées.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.heroes.models import Hero, Map


class GameSession(models.Model):
    """
    Enregistre une partie jouée par un utilisateur authentifié.
    ally_comp et enemy_comp sont des listes de slugs de héros.
    """

    RESULT_CHOICES = [
        ("win", "Victoire"),
        ("loss", "Défaite"),
        ("draw", "Égalité"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="game_sessions"
    )
    hero_played = models.ForeignKey(
        Hero,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions_played",
        verbose_name="Héros joué",
    )
    map_played = models.ForeignKey(
        Map,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions_played",
        verbose_name="Map jouée",
    )
    result = models.CharField(
        max_length=10, choices=RESULT_CHOICES, verbose_name="Résultat"
    )
    # Liste des slugs des héros alliés (hors soi-même)
    ally_comp = models.JSONField(default=list, verbose_name="Composition alliée")
    # Liste des slugs des héros ennemis
    enemy_comp = models.JSONField(default=list, verbose_name="Composition ennemie")
    notes = models.TextField(blank=True, verbose_name="Notes")
    played_at = models.DateTimeField(auto_now_add=True, verbose_name="Joué le")

    class Meta:
        ordering = ["-played_at"]
        verbose_name = "Partie"
        verbose_name_plural = "Parties"

    def __str__(self):
        hero = self.hero_played.name if self.hero_played else "?"
        map_name = self.map_played.name if self.map_played else "?"
        return f"{self.user.username} – {hero} sur {map_name} ({self.result})"
