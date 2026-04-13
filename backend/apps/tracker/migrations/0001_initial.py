"""
Migration initiale : crée la table GameSession.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("heroes", "0001_initial"),  # app_label Django = "heroes" (dernier segment de apps.heroes)
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("result", models.CharField(
                    choices=[("win", "Victoire"), ("loss", "Défaite"), ("draw", "Égalité")],
                    max_length=10,
                    verbose_name="Résultat",
                )),
                ("ally_comp", models.JSONField(default=list, verbose_name="Composition alliée")),
                ("enemy_comp", models.JSONField(default=list, verbose_name="Composition ennemie")),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                ("played_at", models.DateTimeField(auto_now_add=True, verbose_name="Joué le")),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="game_sessions",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("hero_played", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sessions_played",
                    to="heroes.hero",
                    verbose_name="Héros joué",
                )),
                ("map_played", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="sessions_played",
                    to="heroes.map",
                    verbose_name="Map jouée",
                )),
            ],
            options={"ordering": ["-played_at"], "verbose_name": "Partie", "verbose_name_plural": "Parties"},
        ),
    ]
