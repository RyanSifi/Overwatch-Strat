"""
Migration initiale : crée la table PlayerProfile.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("battletag", models.CharField(
                    blank=True,
                    help_text="Format : Pseudo#12345",
                    max_length=50,
                    verbose_name="BattleTag",
                )),
                ("rank_tank", models.CharField(blank=True, max_length=20, verbose_name="Rang Tank")),
                ("rank_dps", models.CharField(blank=True, max_length=20, verbose_name="Rang DPS")),
                ("rank_support", models.CharField(blank=True, max_length=20, verbose_name="Rang Support")),
                ("most_played", models.JSONField(default=list, verbose_name="Héros les plus joués")),
                ("last_synced", models.DateTimeField(blank=True, null=True, verbose_name="Dernière synchronisation")),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ow_profile",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"verbose_name": "Profil joueur", "verbose_name_plural": "Profils joueurs"},
        ),
    ]
