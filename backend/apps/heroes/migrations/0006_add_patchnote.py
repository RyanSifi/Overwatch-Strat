from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heroes", "0005_add_metacomp"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatchNote",
            fields=[
                ("id",        models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version",   models.CharField(max_length=20, unique=True, verbose_name="Version")),
                ("date",      models.DateField(verbose_name="Date")),
                ("title",     models.CharField(max_length=120, blank=True, verbose_name="Titre")),
                ("summary",   models.TextField(blank=True, verbose_name="Resume")),
                ("changes",   models.JSONField(default=list, verbose_name="Changements")),
                ("is_latest", models.BooleanField(default=False, verbose_name="Patch actuel")),
            ],
            options={"ordering": ["-date"], "verbose_name": "Patch Note", "verbose_name_plural": "Patch Notes"},
        ),
    ]
