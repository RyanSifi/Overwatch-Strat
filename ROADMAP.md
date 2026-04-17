# OW Coach — Roadmap & Suivi du projet

## Stack technique
- **Backend** : Django 5 + DRF + PostgreSQL (port 5433) + Redis
- **Frontend web** : React 18 + Vite + Zustand + React Router v6 + Tailwind CSS
- **Frontend mobile** : React Native + Expo + NativeWind + React Navigation
- **IA** : Claude claude-sonnet-4-6 (via proxy Django)
- **Stats OW** : OverFast API

---

## Étapes

### Backend
- [x] **Étape 1** — Settings, models, migrations (`Hero`, `Map`, `GameSession`, `PlayerProfile`)
- [x] **Étape 2** — Fixtures : 47 héros + 18 maps avec tiers, counters, phases
- [x] **Étape 3** — 14 endpoints REST (heroes, maps, counters, coach IA, tracker, auth, profiles)

### Frontend web
- [x] **Étape 4** — Setup Vite + Tailwind + Zustand + React Router
- [ ] **Étape 5** — Composants de base (`HeroCard`, `HeroPicker`, `RoleFilter`, `TierBadge`, `MapSelector`)
- [ ] **Étape 6** — Page `CounterPicker` (comp ennemie → suggestions par rôle)
- [ ] **Étape 7** — Page `Guide` (map + phase → picks recommandés)
- [ ] **Étape 8** — Page `TierList` (filtrable rôle / style / map)
- [ ] **Étape 9** — Page `Tracker` + graphiques Recharts
- [ ] **Étape 10** — Page `Coach IA` (analyse de composition)
- [ ] **Étape 11** — Mode `Overlay` (fenêtre 400px, Alt+O)
- [ ] **Étape 12** — Page `Profile` + sync OverFast API

### Frontend mobile
- [ ] **Étape 13** — Setup Expo + NativeWind + React Navigation
- [ ] **Étape 14** — Screens : Guide, Counter, TierList, Tracker, Coach

---

## Démarrage local

### Backend
```bash
# Démarre les containers Docker
docker start owcoach-pg owcoach-redis

# Lance le serveur Django
cd backend
venv\Scripts\activate        # Windows
python manage.py runserver   # http://localhost:8000
```

### Frontend web
```bash
cd frontend-web
npm install
npm run dev                  # http://localhost:5173
```

### Frontend mobile
```bash
cd frontend-mobile
npm install
npx expo start
```

---

## Endpoints API

| Méthode | URL | Auth | Description |
|---------|-----|------|-------------|
| GET | `/api/heroes/` | Non | Liste des héros (filtres: role, tier, style) |
| GET | `/api/heroes/<slug>/` | Non | Détail d'un héros |
| GET | `/api/heroes/<slug>/counters/` | Non | Counters favorables/défavorables |
| GET | `/api/maps/` | Non | Liste des maps |
| GET | `/api/maps/<slug>/guide/` | Non | Phases + picks recommandés |
| POST | `/api/counters/suggest/` | Non | Counter-picker |
| POST | `/api/coach/analyze/` | Non | Analyse IA Claude |
| POST | `/api/auth/register/` | Non | Inscription |
| POST | `/api/auth/login/` | Non | Connexion (token) |
| GET/POST | `/api/tracker/sessions/` | Oui | Historique parties |
| DELETE | `/api/tracker/sessions/<id>/` | Oui | Supprime une partie |
| GET | `/api/tracker/stats/` | Oui | Statistiques & win rates |
| GET/PATCH | `/api/profiles/me/` | Oui | Profil joueur |
| POST | `/api/profiles/sync/` | Oui | Sync OverFast API |

---

## Variables d'environnement (`backend/.env`)

```env
DJANGO_SECRET_KEY=...
DATABASE_URL=postgresql://owcoach:owcoach@localhost:5433/owcoach
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
DEBUG=True
```
