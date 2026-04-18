"""
Management command : peuple le champ synergies de chaque héros.
Usage : python manage.py seed_synergies
"""
from django.core.management.base import BaseCommand
from apps.heroes.models import Hero


# ── Données de synergies ─────────────────────────────────────────────────────
# Format : { "slug-héros": { "slug-allié": score (1-20) } }
# Score élevé = synergie très forte (ex. Nano Blade = 20)
SYNERGIES_DATA = {
    "ana": {
        "genji":       20,
        "reinhardt":   18,
        "reaper":      18,
        "soldier-76":  16,
        "winston":     15,
        "roadhog":     14,
        "junker-queen":13,
        "dva":         12,
    },
    "genji": {
        "ana":         20,
        "zenyatta":    16,
        "kiriko":      15,
        "lucio":       14,
        "mercy":       12,
    },
    "lucio": {
        "reinhardt":   18,
        "winston":     16,
        "dva":         15,
        "junker-queen":15,
        "genji":       14,
        "tracer":      14,
        "mauga":       13,
        "wrecking-ball":13,
    },
    "mercy": {
        "pharah":      20,
        "echo":        16,
        "bastion":     15,
        "soldier-76":  14,
        "reinhardt":   12,
    },
    "reinhardt": {
        "lucio":       18,
        "zarya":       18,
        "ana":         18,
        "brigitte":    16,
        "zenyatta":    14,
        "moira":       14,
        "junkrat":     13,
    },
    "zarya": {
        "hanzo":       20,
        "pharah":      18,
        "cassidy":     17,
        "reinhardt":   18,
        "reaper":      16,
        "lucio":       14,
        "mei":         15,
    },
    "winston": {
        "tracer":      18,
        "lucio":       16,
        "dva":         16,
        "genji":       15,
        "kiriko":      14,
        "sombra":      13,
    },
    "dva": {
        "lucio":       15,
        "winston":     16,
        "tracer":      14,
        "ana":         12,
        "genji":       13,
    },
    "zenyatta": {
        "genji":       16,
        "widowmaker":  16,
        "tracer":      15,
        "reaper":      14,
        "sojourn":     16,
    },
    "kiriko": {
        "genji":       15,
        "tracer":      14,
        "winston":     14,
        "lucio":       13,
        "reaper":      12,
    },
    "brigitte": {
        "reinhardt":   16,
        "zarya":       15,
        "lucio":       16,
        "junker-queen":15,
        "mauga":       14,
        "roadhog":     13,
    },
    "orisa": {
        "bastion":     18,
        "reaper":      16,
        "hanzo":       14,
        "cassidy":     15,
        "junkrat":     13,
    },
    "sigma": {
        "sojourn":     16,
        "ashe":        15,
        "ana":         14,
        "zenyatta":    14,
        "widowmaker":  13,
    },
    "roadhog": {
        "ana":         14,
        "cassidy":     16,
        "moira":       13,
        "zenyatta":    14,
    },
    "junker-queen": {
        "lucio":       15,
        "brigitte":    15,
        "ana":         14,
        "moira":       13,
    },
    "ramattra": {
        "reaper":      16,
        "moira":       15,
        "ana":         14,
        "zenyatta":    13,
    },
    "mauga": {
        "brigitte":    14,
        "lucio":       13,
        "ana":         14,
        "moira":       14,
    },
    "wrecking-ball": {
        "tracer":      15,
        "lucio":       14,
        "genji":       13,
        "sombra":      14,
    },
    "tracer": {
        "winston":     18,
        "lucio":       14,
        "zenyatta":    15,
        "kiriko":      14,
        "wrecking-ball":15,
    },
    "soldier-76": {
        "ana":         16,
        "mercy":       14,
        "baptiste":    15,
        "lucio":       12,
    },
    "sojourn": {
        "zenyatta":    16,
        "sigma":       16,
        "lucio":       13,
        "kiriko":      15,
    },
    "ashe": {
        "baptiste":    15,
        "sigma":       15,
        "zenyatta":    14,
        "widowmaker":  13,
    },
    "widowmaker": {
        "zenyatta":    16,
        "ashe":        13,
        "sombra":      15,
        "hanzo":       12,
    },
    "hanzo": {
        "zarya":       20,
        "lucio":       14,
        "sigma":       14,
        "widowmaker":  12,
    },
    "pharah": {
        "mercy":       20,
        "baptiste":    16,
        "zarya":       14,
        "ana":         15,
    },
    "junkrat": {
        "reinhardt":   13,
        "orisa":       13,
        "mei":         14,
    },
    "bastion": {
        "mercy":       15,
        "orisa":       18,
        "reinhardt":   15,
        "baptiste":    14,
    },
    "reaper": {
        "zarya":       16,
        "ramattra":    16,
        "orisa":       15,
        "moira":       14,
        "ana":         18,
    },
    "symmetra": {
        "bastion":     15,
        "torbjorn":    14,
        "mei":         14,
        "reinhardt":   13,
    },
    "sombra": {
        "wrecking-ball":14,
        "reaper":      14,
        "tracer":      13,
        "winston":     13,
    },
    "moira": {
        "reaper":      14,
        "reinhardt":   14,
        "ramattra":    15,
        "junker-queen":13,
        "mauga":       14,
    },
    "baptiste": {
        "soldier-76":  15,
        "pharah":      16,
        "reinhardt":   14,
        "ana":         13,
        "ashe":        15,
    },
    "cassidy": {
        "zarya":       17,
        "orisa":       15,
        "ana":         14,
        "sigma":       13,
    },
    "torbjorn": {
        "reinhardt":   14,
        "symmetra":    14,
        "mercy":       13,
        "orisa":       13,
    },
    "mei": {
        "zarya":       15,
        "hanzo":       15,
        "junkrat":     14,
        "reinhardt":   13,
    },
    "echo": {
        "mercy":       16,
        "ana":         15,
        "zenyatta":    14,
        "zarya":       14,
    },
    "venture": {
        "lucio":       13,
        "ana":         13,
        "kiriko":      13,
    },
    # Nouveaux héros
    "hazard": {
        "lucio":       14,
        "ana":         13,
        "brigitte":    13,
        "junker-queen":12,
    },
    "domina": {
        "zenyatta":    13,
        "ana":         14,
        "reaper":      12,
        "moira":       13,
    },
    "anran": {
        "reinhardt":   14,
        "junker-queen":13,
        "mauga":       14,
        "orisa":       12,
    },
    "mizuki": {
        "tracer":      13,
        "genji":       14,
        "kiriko":      12,
        "wrecking-ball":13,
    },
    "freja": {
        "zenyatta":    14,
        "sigma":       13,
        "ana":         13,
    },
    "sierra": {
        "zenyatta":    14,
        "orisa":       13,
        "baptiste":    12,
    },
    "wuyang": {
        "lucio":       13,
        "brigitte":    12,
        "ana":         13,
    },
    "jetpack-cat": {
        "lucio":       14,
        "winston":     13,
        "tracer":      13,
    },
    "vendetta": {
        "sombra":      14,
        "tracer":      13,
        "wrecking-ball":12,
    },
    "emre": {
        "reinhardt":   13,
        "zarya":       13,
        "orisa":       12,
    },
}


class Command(BaseCommand):
    help = "Peuple le champ synergies de chaque héros OW2."

    def handle(self, *args, **options):
        updated = 0
        skipped = 0

        for slug, syns in SYNERGIES_DATA.items():
            try:
                hero = Hero.objects.get(slug=slug)
                hero.synergies = syns
                hero.save(update_fields=["synergies"])
                self.stdout.write(self.style.SUCCESS(f"  ✓ {hero.name}"))
                updated += 1
            except Hero.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠ slug '{slug}' introuvable — ignoré"))
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Synergies seedées : {updated} héros mis à jour, {skipped} ignorés."
            )
        )
