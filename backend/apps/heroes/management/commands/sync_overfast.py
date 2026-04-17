"""
Commande Django : python manage.py sync_overfast

Synchronise les heros depuis l'OverFast API :
  - Met a jour icon_url (portrait officiel Blizzard)
  - Met a jour les fixtures heroes.json
  - Ajoute les nouveaux heros avec --add-missing
"""
import json
import time
from pathlib import Path

import requests
from django.core.management.base import BaseCommand

from apps.heroes.models import Hero

OVERFAST_BASE  = "https://overfast-api.tekrop.fr"
FIXTURES_PATH  = Path(__file__).resolve().parents[2] / "fixtures" / "heroes.json"

ROLE_MAP = {
    "damage": "dps",
    "tank":   "tank",
    "support":"support",
}

NEW_HERO_DEFAULTS = {
    "subrole": "hybrid",
    "tier":    "B",
    "styles":  ["brawl"],
    "counters": {},
    "is_new":  True,
}


class Command(BaseCommand):
    help = "Synchronise portraits des heros depuis OverFast API"

    def add_arguments(self, parser):
        parser.add_argument("--add-missing", action="store_true",
                            help="Ajoute les heros OverFast absents de la DB")
        parser.add_argument("--update-fixtures", action="store_true",
                            help="Met aussi a jour le fichier heroes.json")

    def handle(self, *args, **options):
        self.stdout.write("Recuperation des heros depuis OverFast...")
        try:
            resp = requests.get(f"{OVERFAST_BASE}/heroes?locale=fr-fr", timeout=10)
            resp.raise_for_status()
            ow_heroes = resp.json()
        except Exception as e:
            self.stderr.write(f"Erreur OverFast /heroes : {e}")
            return

        self.stdout.write(f"  {len(ow_heroes)} heros recuperes")

        updated   = 0
        skipped   = 0
        added     = 0
        not_found = []

        for ow in ow_heroes:
            key      = ow["key"]
            portrait = ow.get("portrait", "")
            role     = ROLE_MAP.get(ow.get("role", ""), "dps")
            name     = ow.get("name", key.replace("-", " ").title())

            hero = Hero.objects.filter(slug=key).first()

            if hero:
                if portrait and hero.icon_url != portrait:
                    hero.icon_url = portrait
                    hero.save()
                    updated += 1
                    self.stdout.write(f"  [OK] {name}")
                else:
                    skipped += 1
            else:
                not_found.append(key)
                if options["add_missing"]:
                    last_pk = Hero.objects.order_by("-pk").values_list("pk", flat=True).first() or 0
                    Hero.objects.create(
                        pk=last_pk + 1,
                        name=name,
                        slug=key,
                        role=role,
                        icon_url=portrait,
                        **NEW_HERO_DEFAULTS,
                    )
                    added += 1
                    self.stdout.write(f"  [NEW] {name} (pk={last_pk + 1})")

            time.sleep(0.05)

        self.stdout.write(
            f"\nMis a jour: {updated} | Inchanges: {skipped} | "
            f"Ajoutes: {added} | Absents DB: {not_found}"
        )

        if options["update_fixtures"]:
            self._update_fixtures()

    def _update_fixtures(self):
        if not FIXTURES_PATH.exists():
            self.stderr.write(f"Fixtures non trouvees : {FIXTURES_PATH}")
            return

        with open(FIXTURES_PATH, encoding="utf-8") as f:
            data = json.load(f)

        heroes_db = {h.slug: h for h in Hero.objects.all()}

        for item in data:
            if item.get("model") != "heroes.hero":
                continue
            slug = item["fields"].get("slug")
            if slug in heroes_db:
                item["fields"]["icon_url"] = heroes_db[slug].icon_url

        with open(FIXTURES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write("[OK] Fixtures heroes.json mises a jour")
