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
    # Synergies : dict slug→score (1-20). Score élevé = synergie forte.
    synergies = models.JSONField(default=dict, verbose_name="Synergies")
    DIFFICULTY_CHOICES = [
        (1, "Facile"),
        (2, "Moyen"),
        (3, "Difficile"),
    ]

    # Héros introduits en saison 1 2026 (Domina, Hazard, Anran, Mizuki, Fika)
    is_new = models.BooleanField(default=False, verbose_name="Nouveau héros")
    icon_url = models.URLField(blank=True, verbose_name="URL icône")
    # Difficulté de prise en main : 1=Facile, 2=Moyen, 3=Difficile
    difficulty = models.IntegerField(
        choices=DIFFICULTY_CHOICES, default=2, verbose_name="Difficulté"
    )

    class Meta:
        ordering = ["role", "name"]
        verbose_name = "Héros"
        verbose_name_plural = "Héros"

    def __str__(self):
        return f"{self.name} ({self.role})"


class MetaComp(models.Model):
    """
    Composition méta du patch actuel.
    Chaque comp a un style, un tier, et une liste de héros recommandés.
    """
    STYLE_CHOICES = [
        ("dive",   "Dive"),
        ("brawl",  "Brawl"),
        ("poke",   "Poke"),
        ("rush",   "Rush"),
        ("hybrid", "Hybrid"),
    ]
    TIER_CHOICES = [("S","S"),("A","A"),("B","B"),("C","C")]

    name        = models.CharField(max_length=80, verbose_name="Nom")
    style       = models.CharField(max_length=20, choices=STYLE_CHOICES)
    tier        = models.CharField(max_length=5,  choices=TIER_CHOICES, default="A")
    description = models.TextField(blank=True)
    # ["slug1","slug2","slug3","slug4","slug5"]
    heroes      = models.JSONField(default=list, verbose_name="Héros")
    patch       = models.CharField(max_length=20, default="S14", verbose_name="Patch")
    win_rate    = models.FloatField(default=0.0, verbose_name="Win rate %")
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-tier", "style", "name"]
        verbose_name = "Comp méta"
        verbose_name_plural = "Comps méta"

    def __str__(self):
        return f"{self.name} ({self.style} — {self.tier})"


class PatchNote(models.Model):
    """
    Note de patch par version.
    changes : liste de { "hero_slug": str, "type": "buff"|"nerf"|"rework"|"fix", "text": str }
    """
    version     = models.CharField(max_length=20, unique=True, verbose_name="Version")
    date        = models.DateField(verbose_name="Date")
    title       = models.CharField(max_length=120, blank=True, verbose_name="Titre")
    summary     = models.TextField(blank=True, verbose_name="Résumé")
    changes     = models.JSONField(default=list, verbose_name="Changements")
    is_latest   = models.BooleanField(default=False, verbose_name="Patch actuel")

    class Meta:
        ordering = ["-date"]
        verbose_name = "Patch Note"
        verbose_name_plural = "Patch Notes"

    def __str__(self):
        return f"Patch {self.version} — {self.date}"


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
        ("clash", "Clash"),
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
