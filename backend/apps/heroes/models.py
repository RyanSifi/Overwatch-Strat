"""
Modèles pour les héros et les maps Overwatch.
"""
from django.db import models


class Hero(models.Model):
    """
    Représente un héros Overwatch avec ses attributs méta.
    Les counters sont stockés sous forme de dict JSON :
    { "slug-ennemi": score_entier }  (score de -20 à +20)
    Un score positif signifie que ce héros est bon contre l'ennemi.
    """

    ROLE_CHOICES = [
        ("tank", "Tank"),
        ("dps", "DPS"),
        ("support", "Support"),
    ]

    SUBROLE_CHOICES = [
        # Tanks
        ("bruiser", "Bruiser"),
        ("initiator", "Initiator"),
        ("stalwart", "Stalwart"),
        # DPS
        ("flanker", "Flanker"),
        ("recon", "Recon"),
        ("sharpshooter", "Sharpshooter"),
        ("specialist", "Specialist"),
        # Supports
        ("medic", "Medic"),
        ("survivor", "Survivor"),
        ("tactician", "Tactician"),
    ]

    TIER_CHOICES = [
        ("S", "S"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Rôle")
    subrole = models.CharField(
        max_length=20, choices=SUBROLE_CHOICES, verbose_name="Sous-rôle"
    )
    tier = models.CharField(
        max_length=5, choices=TIER_CHOICES, default="B", verbose_name="Tier"
    )
    # Styles de jeu auxquels ce héros contribue (ex: ["brawl", "poke"])
    styles = models.JSONField(default=list, verbose_name="Styles de jeu")
    # Dict slug→score : score positif = ce héros counter l'ennemi
    counters = models.JSONField(default=dict, verbose_name="Counters")
    # Points forts/faibles : liste de { "label": str, "rating": "++" | "+" | "-" | "--" }
    traits = models.JSONField(default=list, verbose_name="Traits")
    # Héros introduits en saison 1 2026 (Domina, Hazard, Anran, Mizuki, Fika)
    is_new = models.BooleanField(default=False, verbose_name="Nouveau héros")
    icon_url = models.URLField(blank=True, verbose_name="URL icône")

    class Meta:
        ordering = ["role", "name"]
        verbose_name = "Héros"
        verbose_name_plural = "Héros"

    def __str__(self):
        return f"{self.name} ({self.role})"


class Map(models.Model):
    """
    Représente une map Overwatch avec ses phases et les picks recommandés.
    Le champ 'phases' est un tableau JSON de la forme :
    [
      {
        "name": "Point A",
        "style": "poke",
        "notes": "Longues lignes de mire côté attaque",
        "recommended": {
          "tank": ["sigma", "domina"],
          "dps": ["ashe", "sojourn"],
          "support": ["ana", "zenyatta"]
        }
      },
      ...
    ]
    """

    MAP_TYPE_CHOICES = [
        ("escort", "Escort"),
        ("control", "Control"),
        ("hybrid", "Hybrid"),
        ("push", "Push"),
        ("flashpoint", "Flashpoint"),
    ]

    name = models.CharField(max_length=50, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    map_type = models.CharField(
        max_length=20, choices=MAP_TYPE_CHOICES, verbose_name="Type"
    )
    phases = models.JSONField(default=list, verbose_name="Phases")

    class Meta:
        ordering = ["map_type", "name"]
        verbose_name = "Map"
        verbose_name_plural = "Maps"

    def __str__(self):
        return f"{self.name} ({self.map_type})"
