"""
Modèle pour le profil Overwatch d'un utilisateur.
"""
from django.db import models
from django.contrib.auth.models import User


class PlayerProfile(models.Model):
    """
    Profil Overwatch lié au compte utilisateur Django.
    Les rangs sont stockés sous forme de chaîne (ex : "Gold 3", "Platinum 1").
    most_played est une liste de slugs de héros (ex : ["zarya", "dva", "ana"]).
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="ow_profile"
    )
    battletag = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="BattleTag",
        help_text="Format : Pseudo#12345",
    )
    rank_tank = models.CharField(
        max_length=20, blank=True, verbose_name="Rang Tank"
    )
    rank_dps = models.CharField(
        max_length=20, blank=True, verbose_name="Rang DPS"
    )
    rank_support = models.CharField(
        max_length=20, blank=True, verbose_name="Rang Support"
    )
    # Slugs des héros les plus joués (issus d'OverFast API)
    most_played = models.JSONField(default=list, verbose_name="Héros les plus joués")
    last_synced = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière synchronisation"
    )

    class Meta:
        verbose_name = "Profil joueur"
        verbose_name_plural = "Profils joueurs"

    def __str__(self):
        return f"Profil de {self.user.username} ({self.battletag or 'sans BattleTag'})"
