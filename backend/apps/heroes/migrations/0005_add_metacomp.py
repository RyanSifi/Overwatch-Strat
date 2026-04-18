from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heroes", "0004_add_synergies_to_hero"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetaComp",
            fields=[
                ("id",          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name",        models.CharField(max_length=80, verbose_name="Nom")),
                ("style",       models.CharField(max_length=20, choices=[("dive","Dive"),("brawl","Brawl"),("poke","Poke"),("rush","Rush"),("hybrid","Hybrid")])),
                ("tier",        models.CharField(max_length=5, choices=[("S","S"),("A","A"),("B","B"),("C","C")], default="A")),
                ("description", models.TextField(blank=True)),
                ("heroes",      models.JSONField(default=list, verbose_name="Héros")),
                ("patch",       models.CharField(max_length=20, default="S14", verbose_name="Patch")),
                ("win_rate",    models.FloatField(default=0.0, verbose_name="Win rate %")),
                ("is_featured", models.BooleanField(default=False)),
            ],
            options={"ordering": ["-tier", "style", "name"], "verbose_name": "Comp méta", "verbose_name_plural": "Comps méta"},
        ),
    ]
