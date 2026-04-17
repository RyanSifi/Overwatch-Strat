"""
Views pour les héros, maps et counter-picker.
Tous les endpoints publics (aucune authentification requise).
"""
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Hero, Map
from .serializers import HeroSerializer, HeroListSerializer, MapSerializer


# ─── Héros ───────────────────────────────────────────────────────────────────

class HeroListView(generics.ListAPIView):
    """
    GET /api/heroes/
    Retourne tous les héros. Supporte les filtres :
    ?role=tank|dps|support
    ?tier=S|A|B|C|D
    ?style=brawl|dive|poke
    ?is_new=true
    """
    permission_classes = [AllowAny]
    serializer_class   = HeroListSerializer
    pagination_class   = None  # Retourne tous les héros sans pagination

    def get_queryset(self):
        qs = Hero.objects.all()
        role   = self.request.query_params.get("role")
        tier   = self.request.query_params.get("tier")
        style  = self.request.query_params.get("style")
        is_new = self.request.query_params.get("is_new")

        if role:
            qs = qs.filter(role=role)
        if tier:
            qs = qs.filter(tier=tier)
        if style:
            # JSONField contains : filtre les héros dont styles contient la valeur
            qs = qs.filter(styles__contains=[style])
        if is_new and is_new.lower() == "true":
            qs = qs.filter(is_new=True)
        return qs


class HeroDetailView(generics.RetrieveAPIView):
    """GET /api/heroes/<slug>/"""
    permission_classes = [AllowAny]
    serializer_class   = HeroSerializer
    queryset           = Hero.objects.all()
    lookup_field       = "slug"


@api_view(["GET"])
@permission_classes([AllowAny])
def hero_counters(request, slug):
    """
    GET /api/heroes/<slug>/counters/
    Retourne les counters d'un héros avec le détail de chaque héros counter.
    Sépare en deux listes : favorable (score > 0) et défavorable (score < 0).
    """
    try:
        hero = Hero.objects.get(slug=slug)
    except Hero.DoesNotExist:
        return Response({"error": f"Héros '{slug}' introuvable."}, status=status.HTTP_404_NOT_FOUND)

    favorable   = {}
    defavorable = {}

    for enemy_slug, score in hero.counters.items():
        try:
            enemy = Hero.objects.get(slug=enemy_slug)
            data  = {
                "slug":    enemy.slug,
                "name":    enemy.name,
                "role":    enemy.role,
                "tier":    enemy.tier,
                "icon_url": enemy.icon_url,
                "score":   score,
            }
            if score > 0:
                favorable[enemy_slug] = data
            else:
                defavorable[enemy_slug] = data
        except Hero.DoesNotExist:
            # Ignore les slugs obsolètes dans les fixtures
            continue

    # Trie par score décroissant / croissant
    favorable_sorted   = sorted(favorable.values(),   key=lambda x: x["score"], reverse=True)
    defavorable_sorted = sorted(defavorable.values(), key=lambda x: x["score"])

    return Response({
        "hero":       HeroSerializer(hero).data,
        "favorable":  favorable_sorted,
        "defavorable": defavorable_sorted,
    })


# ─── Maps ────────────────────────────────────────────────────────────────────

class MapListView(generics.ListAPIView):
    """
    GET /api/maps/
    Retourne toutes les maps. Filtre optionnel : ?map_type=escort|control|hybrid|push|flashpoint
    """
    permission_classes = [AllowAny]
    serializer_class   = MapSerializer
    pagination_class   = None  # Retourne toutes les maps sans pagination

    def get_queryset(self):
        qs       = Map.objects.all()
        map_type = self.request.query_params.get("map_type")
        if map_type:
            qs = qs.filter(map_type=map_type)
        return qs


@api_view(["GET"])
@permission_classes([AllowAny])
def map_guide(request, slug):
    """
    GET /api/maps/<slug>/guide/
    Retourne le guide complet d'une map : chaque phase avec style, notes
    et les héros recommandés enrichis (tier, subrole, etc.).
    """
    try:
        map_obj = Map.objects.get(slug=slug)
    except Map.DoesNotExist:
        return Response({"error": f"Map '{slug}' introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # Enrichit les picks recommandés avec les données complètes des héros
    enriched_phases = []
    for phase in map_obj.phases:
        enriched_recommended = {}
        for role, slugs in phase.get("recommended", {}).items():
            heroes_data = []
            for hero_slug in slugs:
                try:
                    h = Hero.objects.get(slug=hero_slug)
                    heroes_data.append({
                        "slug":     h.slug,
                        "name":     h.name,
                        "tier":     h.tier,
                        "subrole":  h.subrole,
                        "icon_url": h.icon_url,
                    })
                except Hero.DoesNotExist:
                    heroes_data.append({"slug": hero_slug, "name": hero_slug})
            enriched_recommended[role] = heroes_data

        enriched_phases.append({
            "name":        phase.get("name"),
            "style":       phase.get("style"),
            "notes":       phase.get("notes", ""),
            "recommended": enriched_recommended,
        })

    return Response({
        "map":    MapSerializer(map_obj).data,
        "phases": enriched_phases,
    })


# ─── Counter-picker ───────────────────────────────────────────────────────────

# Explications spécifiques par matchup (hero_slug, enemy_slug)
MATCHUP_REASONS = {
    # D.Va
    ("dva", "bastion"):      "La Défense Matricielle absorbe entièrement le feu de Bastion",
    ("dva", "pharah"):       "Les missiles et la Matrice dominent Pharah dans les airs",
    ("dva", "junkrat"):      "La Matrice détruit les grenades et les pneus de Junkrat",
    ("dva", "torbjorn"):     "La Matrice détruit la tourelle de Torbjörn facilement",
    ("dva", "symmetra"):     "La Matrice absorbe les rayons et détruit les tourelles",
    ("dva", "sojourn"):      "La Matrice bloque les tirs chargés de Sojourn",
    ("dva", "hanzo"):        "La Matrice détruit les flèches et les dragons",
    ("dva", "ashe"):         "Plonge sur Ashe et absorbe ses tirs avec la Matrice",
    # Winston
    ("winston", "widowmaker"): "Saut direct sur Widowmaker, elle ne peut pas fuir",
    ("winston", "tracer"):     "Le tesla suit Tracer même en déplacement rapide",
    ("winston", "genji"):      "Le tesla inflige des dégâts continus, contrant la mobilité de Genji",
    ("winston", "sojourn"):    "Dive sur Sojourn avant qu'elle charge ses tirs",
    ("winston", "hanzo"):      "Saut sur Hanzo avant qu'il repositionne",
    ("winston", "ashe"):       "Dive sur Ashe et perturbe son positionnement",
    # Zarya
    ("zarya", "mei"):          "La bulle protège les alliés du freeze et brise les Cryo-Congels",
    ("zarya", "cassidy"):      "La bulle annule la Grenade Magnétique de Cassidy",
    ("zarya", "genji"):        "La bulle annule le deflect et les shurikens",
    ("zarya", "tracer"):       "La bulle sauve les alliés piégés par les Pulse Bomb",
    ("zarya", "reaper"):       "La bulle réduit les dégâts de Faucheur au corps à corps",
    # Sigma
    ("sigma", "pharah"):       "Le bouclier bloque les roquettes, l'accrétion neutralise Pharah",
    ("sigma", "bastion"):      "Le bouclier absorbe le feu de Bastion, Sigma contre à distance",
    ("sigma", "ashe"):         "Le bouclier bloque les tirs longue portée d'Ashe",
    ("sigma", "hanzo"):        "Le bouclier bloque les flèches et les dragons de Hanzo",
    ("sigma", "soldier-76"):   "Le bouclier bloque les rafales de Soldat : 76",
    ("sigma", "echo"):         "L'accrétion interrompt Echo en vol",
    ("sigma", "widowmaker"):   "Le bouclier force Widowmaker à changer de position",
    # Reinhardt
    ("reinhardt", "bastion"):  "Le Bouclier de Barrière absorbe le feu de Bastion",
    ("reinhardt", "ashe"):     "Le bouclier bloque entièrement les tirs longs d'Ashe",
    ("reinhardt", "soldier-76"): "Le bouclier contient Soldat : 76 à distance",
    ("reinhardt", "cassidy"):  "Le bouclier bloque les tirs et force Cassidy au corps à corps",
    ("reinhardt", "junkrat"):  "Le bouclier absorbe les grenades et le pneu de Junkrat",
    ("reinhardt", "mei"):      "Le bouclier empêche Mei de geler l'équipe à distance",
    # Orisa
    ("orisa", "mei"):          "Fortifier annule le gel de Mei, Orisa n'est pas ralentie",
    ("orisa", "cassidy"):      "Fortifier réduit massivement les dégâts de Cassidy",
    ("orisa", "soldier-76"):   "La javeline interrompt le Sprint tactique de Soldat : 76",
    ("orisa", "ashe"):         "La lance de Orisa repousse Ashe et son cheval Bob",
    # Hazard
    ("hazard", "venture"):     "Hazard est très mobile, réplique à la mobilité de Venture",
    ("hazard", "reaper"):      "Les piques tiennent Faucheur à distance",
    ("hazard", "cassidy"):     "La mobilité de Hazard évite les flashbangs de Cassidy",
    ("hazard", "soldier-76"):  "Hazard prend les angles pour éviter les tirs de Soldat : 76",
    # Ramattra
    ("ramattra", "mei"):       "La forme Nemesis résiste au freeze, Ramattra s'approche sans crainte",
    ("ramattra", "cassidy"):   "La forme Nemesis absorbe les dégâts de Cassidy",
    ("ramattra", "reaper"):    "La forme Nemesis réduit les dégâts au corps à corps de Faucheur",
    ("ramattra", "venture"):   "L'anneau de blocage neutralise la sortie de terre de Venture",
    # Ana
    ("ana", "sojourn"):        "Fléchette soporifique empêche Sojourn de charger sa Glissade",
    ("ana", "widowmaker"):     "La fléchette endort Widowmaker avant qu'elle vise",
    ("ana", "bastion"):        "Le tir anti-soin annule les soins pendant la forme Tank de Bastion",
    ("ana", "ashe"):           "La grenade anti-soin empêche Ashe de récupérer après un duel",
    ("ana", "soldier-76"):     "La grenade et le tir anti-soin contrent le Biotic Field",
    ("ana", "hanzo"):          "La fléchette soporifique interrompt la concentration de Hanzo",
    ("ana", "venture"):        "La fléchette endort Venture à la sortie de son terrier",
    ("ana", "junkrat"):        "Tir anti-soin sur le Junkrat empêche toute récupération",
    # Baptiste
    ("baptiste", "bastion"):   "Champ d'immortalité permet à l'équipe de survivre à la rafale de Bastion",
    ("baptiste", "sojourn"):   "Le Champ d'immortalité contrecarre les one-shots de Sojourn",
    ("baptiste", "torbjorn"):  "La lampe détruit facilement la tourelle de Torbjörn",
    ("baptiste", "soldier-76"):"Le tir en rafale de Baptiste domine à mi-portée face à Soldat",
    ("baptiste", "ashe"):      "Le Champ d'immortalité annule les picks d'Ashe",
    ("baptiste", "junkrat"):   "Le Champ d'immortalité absorbe les combos de Junkrat",
    # Kiriko
    ("kiriko", "mei"):         "Suzu nettoie instantanément le gel de Mei sur tes alliés",
    ("kiriko", "sombra"):      "Suzu supprime le hack de Sombra",
    ("kiriko", "cassidy"):     "Suzu supprime la Grenade Magnétique de Cassidy",
    ("kiriko", "soldier-76"):  "La téléportation de Kiriko permet d'esquiver les ulti",
    ("kiriko", "sojourn"):     "Suzu peut cleanse les effets de ralentissement de Sojourn",
    ("kiriko", "venture"):     "Suzu nettoie les effets de Venture à la sortie du sol",
    ("kiriko", "widowmaker"):  "Suzu protège les alliés visés par Widowmaker",
    # Zenyatta
    ("zenyatta", "bastion"):   "L'Orbe de discorde multiplie les dégâts sur Bastion",
    ("zenyatta", "widowmaker"):"L'Orbe de discorde force Widowmaker à se repositionner",
    ("zenyatta", "cassidy"):   "L'Orbe de discorde compense l'armure lourde de Cassidy",
    ("zenyatta", "ashe"):      "L'Orbe de discorde rend Ashe vulnérable malgré sa portée",
    ("zenyatta", "hanzo"):     "L'Orbe de discorde sur Hanzo amplifie tous les tirs",
    ("zenyatta", "soldier-76"):"L'Orbe de discorde annihile rapidement Soldat : 76",
    ("zenyatta", "junkrat"):   "Transcendance survit aux combos de Junkrat",
    # Brigitte
    ("brigitte", "tracer"):    "Coup de bouclier et fouet interrompent les Blink de Tracer",
    ("brigitte", "genji"):     "Coup de bouclier interrompt les déflexions de Genji",
    ("brigitte", "reaper"):    "L'armure de pack de soin réduit les dégâts de Faucheur",
    ("brigitte", "mei"):       "Les packs d'armure protègent l'équipe du gel de Mei",
    ("brigitte", "venture"):   "Coup de bouclier interrompt Venture à la sortie de terre",
    ("brigitte", "sombra"):    "La résistance empêche Sombra de te one-shot facilement",
    # Lucio
    ("lucio", "widowmaker"):   "Vitesse de groupe permet d'éviter les lignes de mire",
    ("lucio", "symmetra"):     "La vitesse annule les turelles de Symmetra rapidement",
    ("lucio", "torbjorn"):     "Le boost de vitesse permet de rush et détruire la tourelle",
    ("lucio", "pharah"):       "Le Boop envoie Pharah hors position",
    ("lucio", "bastion"):      "Le boost de vitesse permet d'approcher Bastion en sécurité",
    # Moira
    ("moira", "reaper"):       "Fade annule les téléportations de Faucheur et esquive ses dégâts",
    ("moira", "venture"):      "Fade passe à travers les attaques de Venture",
    ("moira", "mei"):          "Fade nettoie les effets de gel de Mei",
    ("moira", "tracer"):       "La sphère de dégâts suit Tracer partout",
    # Mercy
    ("mercy", "pharah"):       "Amplification des dégâts sur un DPS détruit Pharah depuis le sol",
    ("mercy", "widowmaker"):   "Boost de dégâts + résurrection contrent les picks de Widowmaker",
    ("mercy", "echo"):         "Res d'Echo empêche l'ennemi de prendre l'avantage avec la copie",
}

# Descriptions basées sur le subrole pour les matchups sans raison spécifique
SUBROLE_INTROS = {
    "initiator":  "Initie les combats pour forcer des positions défavorables à l'ennemi",
    "anchor":     "Anchor tank solide — tient le terrain et protège l'équipe",
    "brawler":    "Combat au corps à corps, écrase les ennemis rapprochés",
    "disruptor":  "Perturbe la composition ennemie et gêne leurs rotations",
    "flanker":    "Flanque la backline ennemie et élimine les cibles isolées",
    "sniper":     "Domine à longue portée et contre les héros fixes",
    "area":       "Contrôle les zones et force les ennemis à se disperser",
    "hybrid":     "Polyvalent — s'adapte à plusieurs types de compositions",
    "healer":     "Maintient l'équipe en vie face aux dégâts continus",
    "aggressive": "Soigne tout en harcelant les ennemis en backline",
    "utility":    "Apporte des utilitaires décisifs (cleanse, boost, ulti counter)",
    "survivor":   "Très difficile à éliminer, force l'ennemi à sur-investir",
}

def build_reason(hero, covered_enemies, enemy_name_map, total_score):
    """Génère une explication détaillée pour un counter suggéré."""
    specific_reasons = []
    for enemy_slug in covered_enemies:
        key = (hero.slug, enemy_slug)
        if key in MATCHUP_REASONS:
            specific_reasons.append(MATCHUP_REASONS[key])

    if specific_reasons:
        return " • ".join(specific_reasons)

    # Fallback : explication basée sur le subrole + ennemis couverts
    names = [enemy_name_map.get(s, s) for s in covered_enemies]
    intro = SUBROLE_INTROS.get(hero.subrole, "Bon pick dans cette composition")
    if names:
        return f"{intro}. Efficace contre {', '.join(names)}."
    return intro

@api_view(["POST"])
@permission_classes([AllowAny])
def suggest_counters(request):
    """
    POST /api/counters/suggest/
    Body : { "enemy_heroes": ["domina", "sojourn", "ana"] }

    Algorithme :
    1. Pour chaque héros de la liste ennemie, parcourt TOUS les héros de la BDD.
    2. Si un héros a un score positif contre cet ennemi dans son dict 'counters',
       on ajoute ce score à son score total.
    3. On déduplique et trie par score décroissant.
    4. On retourne les 3 meilleurs par rôle avec explication.
    """
    enemy_slugs = request.data.get("enemy_heroes", [])
    if not enemy_slugs:
        return Response({"error": "Champ 'enemy_heroes' requis."}, status=status.HTTP_400_BAD_REQUEST)
    if len(enemy_slugs) > 6:
        return Response({"error": "Maximum 6 héros ennemis."}, status=status.HTTP_400_BAD_REQUEST)

    # Vérifie que les slugs ennemis existent
    valid_enemy_slugs = []
    for slug in enemy_slugs:
        if Hero.objects.filter(slug=slug).exists():
            valid_enemy_slugs.append(slug)

    if not valid_enemy_slugs:
        return Response({"error": "Aucun héros ennemi valide."}, status=status.HTTP_400_BAD_REQUEST)

    # Calcul des scores agrégés
    # score_map : { hero_slug: { total_score, covered_enemies: [], hero_obj } }
    score_map = {}

    all_heroes = Hero.objects.all()
    for hero in all_heroes:
        # Ignore les héros ennemis eux-mêmes dans les suggestions
        if hero.slug in valid_enemy_slugs:
            continue

        total_score    = 0
        covered        = []

        for enemy_slug in valid_enemy_slugs:
            score = hero.counters.get(enemy_slug, 0)
            if score > 0:
                total_score += score
                covered.append(enemy_slug)

        if total_score > 0:
            score_map[hero.slug] = {
                "hero":           hero,
                "total_score":    total_score,
                "covered_enemies": covered,
            }

    # Trie par score décroissant et regroupe par rôle
    sorted_heroes = sorted(score_map.values(), key=lambda x: x["total_score"], reverse=True)

    # Pré-charge les noms ennemis pour les explications
    enemy_name_map = {}
    for slug in valid_enemy_slugs:
        try:
            enemy_name_map[slug] = Hero.objects.get(slug=slug).name
        except Hero.DoesNotExist:
            enemy_name_map[slug] = slug

    result = {"tank": [], "dps": [], "support": []}

    for entry in sorted_heroes:
        hero  = entry["hero"]
        role  = hero.role
        if role not in result:
            continue
        if len(result[role]) >= 3:
            continue

        reason = build_reason(hero, entry["covered_enemies"], enemy_name_map, entry["total_score"])

        result[role].append({
            "slug":            hero.slug,
            "name":            hero.name,
            "role":            hero.role,
            "subrole":         hero.subrole,
            "tier":            hero.tier,
            "styles":          hero.styles,
            "icon_url":        hero.icon_url,
            "total_score":     entry["total_score"],
            "covered_enemies": entry["covered_enemies"],
            "reason":          reason,
        })

    return Response({
        "enemy_heroes": valid_enemy_slugs,
        "suggestions":  result,
    })
