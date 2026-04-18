from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heroes", "0003_add_difficulty_to_hero"),
    ]

    operations = [
        migrations.AddField(
            model_name="hero",
            name="synergies",
            field=models.JSONField(default=dict, verbose_name="Synergies"),
        ),
    ]
