"""
Migration initiale : crée les tables Hero et Map.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Hero",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True, verbose_name="Nom")),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
                ("role", models.CharField(
                    choices=[("tank", "Tank"), ("dps", "DPS"), ("support", "Support")],
                    max_length=20,
                    verbose_name="Rôle",
                )),
                ("subrole", models.CharField(
                    choices=[
                        ("bruiser", "Bruiser"), ("initiator", "Initiator"), ("stalwart", "Stalwart"),
                        ("flanker", "Flanker"), ("recon", "Recon"), ("sharpshooter", "Sharpshooter"),
                        ("specialist", "Specialist"), ("medic", "Medic"), ("survivor", "Survivor"),
                        ("tactician", "Tactician"),
                    ],
                    max_length=20,
                    verbose_name="Sous-rôle",
                )),
                ("tier", models.CharField(
                    choices=[("S", "S"), ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
                    default="B",
                    max_length=5,
                    verbose_name="Tier",
                )),
                ("styles", models.JSONField(default=list, verbose_name="Styles de jeu")),
                ("counters", models.JSONField(default=dict, verbose_name="Counters")),
                ("is_new", models.BooleanField(default=False, verbose_name="Nouveau héros")),
                ("icon_url", models.URLField(blank=True, verbose_name="URL icône")),
            ],
            options={"ordering": ["role", "name"], "verbose_name": "Héros", "verbose_name_plural": "Héros"},
        ),
        migrations.CreateModel(
            name="Map",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Nom")),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
                ("map_type", models.CharField(
                    choices=[
                        ("escort", "Escort"), ("control", "Control"), ("hybrid", "Hybrid"),
                        ("push", "Push"), ("flashpoint", "Flashpoint"),
                    ],
                    max_length=20,
                    verbose_name="Type",
                )),
                ("phases", models.JSONField(default=list, verbose_name="Phases")),
            ],
            options={"ordering": ["map_type", "name"], "verbose_name": "Map", "verbose_name_plural": "Maps"},
        ),
    ]
