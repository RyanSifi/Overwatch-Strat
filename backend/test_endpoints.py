"""
Script de test des endpoints API OW Coach.
Lance avec : python manage.py shell < test_endpoints.py
Ou directement : python test_endpoints.py (avec DJANGO_SETTINGS_MODULE défini)
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

import json
from rest_framework.test import APIRequestFactory
from rest_framework import renderers
from django.contrib.auth.models import User

factory = APIRequestFactory()

def render(resp):
    resp.accepted_renderer = renderers.JSONRenderer()
    resp.accepted_media_type = "application/json"
    resp.renderer_context = {}
    resp.render()
    return json.loads(resp.content)

results = []

# 1. Liste des héros
try:
    from apps.heroes.views import HeroListView
    r = factory.get("/api/heroes/")
    d = render(HeroListView.as_view()(r))
    results.append(f"OK  GET /api/heroes/           → {d['count']} héros, premier: {d['results'][0]['name']}")
except Exception as e:
    results.append(f"ERR GET /api/heroes/           → {e}")

# 2. Détail héros
try:
    from apps.heroes.views import HeroDetailView
    r = factory.get("/")
    d = render(HeroDetailView.as_view()(r, slug="zarya"))
    results.append(f"OK  GET /api/heroes/zarya/     → tier={d['tier']} styles={d['styles']}")
except Exception as e:
    results.append(f"ERR GET /api/heroes/zarya/     → {e}")

# 3. Counters d'un héros
try:
    from apps.heroes.views import hero_counters
    r = factory.get("/")
    d = render(hero_counters(r, slug="zarya"))
    top = d["favorable"][0]["name"] if d["favorable"] else "?"
    results.append(f"OK  GET /api/heroes/zarya/counters/ → {len(d['favorable'])} favorables, top: {top}")
except Exception as e:
    results.append(f"ERR GET /api/heroes/zarya/counters/ → {e}")

# 4. Liste des maps
try:
    from apps.heroes.views import MapListView
    r = factory.get("/api/maps/")
    d = render(MapListView.as_view()(r))
    results.append(f"OK  GET /api/maps/             → {d['count']} maps")
except Exception as e:
    results.append(f"ERR GET /api/maps/             → {e}")

# 5. Guide d'une map
try:
    from apps.heroes.views import map_guide
    r = factory.get("/")
    d = render(map_guide(r, slug="kings-row"))
    phases = [p["name"] for p in d["phases"]]
    results.append(f"OK  GET /api/maps/kings-row/guide/ → {len(phases)} phases: {phases}")
except Exception as e:
    results.append(f"ERR GET /api/maps/kings-row/guide/ → {e}")

# 6. Counter-picker
try:
    from apps.heroes.views import suggest_counters
    r = factory.post("/", {"enemy_heroes": ["sigma", "sojourn", "ana"]}, format="json")
    d = render(suggest_counters(r))
    tanks = [h["name"] for h in d["suggestions"]["tank"]]
    dps   = [h["name"] for h in d["suggestions"]["dps"]]
    supp  = [h["name"] for h in d["suggestions"]["support"]]
    results.append(f"OK  POST /api/counters/suggest/ → tanks={tanks}")
    results.append(f"                                  dps={dps}")
    results.append(f"                                  support={supp}")
except Exception as e:
    results.append(f"ERR POST /api/counters/suggest/ → {e}")

# 7. Register
try:
    from config.urls import register as reg_view
    # Supprime si existe déjà
    User.objects.filter(username="owplayer").delete()
    r = factory.post("/", {"username": "owplayer", "email": "ow@test.fr", "password": "pass9999"}, format="json")
    d = render(reg_view(r))
    if "token" in d:
        results.append(f"OK  POST /api/auth/register/   → user={d['username']} token={d['token'][:12]}...")
    else:
        results.append(f"ERR POST /api/auth/register/   → {d}")
except Exception as e:
    results.append(f"ERR POST /api/auth/register/   → {e}")

# 8. Login
try:
    from rest_framework.authtoken.views import obtain_auth_token
    r = factory.post("/", {"username": "owplayer", "password": "pass9999"}, format="json")
    d = render(obtain_auth_token(r))
    if "token" in d:
        results.append(f"OK  POST /api/auth/login/      → token={d['token'][:12]}...")
    else:
        results.append(f"ERR POST /api/auth/login/      → {d}")
except Exception as e:
    results.append(f"ERR POST /api/auth/login/      → {e}")

# 9. Tracker stats (authentifié)
try:
    from apps.tracker.views import tracker_stats
    user = User.objects.get(username="owplayer")
    r = factory.get("/")
    r.user = user
    d = render(tracker_stats(r))
    results.append(f"OK  GET /api/tracker/stats/    → total_games={d['total_games']} win_rate={d['win_rate_global']}%")
except Exception as e:
    results.append(f"ERR GET /api/tracker/stats/    → {e}")

# 10. Profil (authentifié)
try:
    from apps.profiles.views import profile_me
    user = User.objects.get(username="owplayer")
    r = factory.get("/")
    r.user = user
    d = render(profile_me(r))
    results.append(f"OK  GET /api/profiles/me/      → battletag='{d['battletag']}' ranks: tank={d['rank_tank']}")
except Exception as e:
    results.append(f"ERR GET /api/profiles/me/      → {e}")

# ── Affichage ──────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("  TESTS ENDPOINTS OW COACH")
print("=" * 65)
for line in results:
    print(line)
print("=" * 65)

errors = [r for r in results if r.startswith("ERR")]
if errors:
    print(f"\n{len(errors)} erreur(s) détectée(s)")
    sys.exit(1)
else:
    print(f"\n✅ {len([r for r in results if r.startswith('OK')])} endpoints validés")
