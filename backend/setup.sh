#!/bin/bash
# Script de démarrage rapide pour le backend OW Coach
# Lance depuis le dossier backend/

set -e

echo "==> Création du virtualenv..."
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

echo "==> Installation des dépendances..."
pip install -r requirements.txt

echo "==> Copie du fichier .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  Remplis les valeurs dans backend/.env avant de continuer !"
fi

echo "==> Application des migrations..."
python manage.py migrate

echo "==> Chargement des fixtures..."
python manage.py loaddata apps/heroes/fixtures/heroes.json
python manage.py loaddata apps/heroes/fixtures/maps.json

echo "==> Création du superutilisateur (optionnel)..."
python manage.py createsuperuser --noinput || true

echo "✅ Backend prêt. Lance : python manage.py runserver"
