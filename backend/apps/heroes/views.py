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
# Format : "[Hero] est fort contre [Ennemi] car [mécanique concrète]"
MATCHUP_REASONS = {
    # ── D.Va ──────────────────────────────────────────────────────────────────
    ("dva", "bastion"):       "D.Va écrase Bastion car sa Défense Matricielle absorbe entièrement sa rafale en mode Artillerie",
    ("dva", "pharah"):        "D.Va domine Pharah car ses missiles air-air et sa Matrice la détruisent dans les airs",
    ("dva", "junkrat"):       "D.Va neutralise Junkrat car la Matrice détruit ses grenades et ses pneus en plein vol",
    ("dva", "torbjorn"):      "D.Va contre Torbjörn car elle plonge sur la tourelle et la détruit avec la Matrice",
    ("dva", "symmetra"):      "D.Va efface Symmetra car la Matrice absorbe ses rayons et ses tourelles ne font rien",
    ("dva", "sojourn"):       "D.Va contrecarre Sojourn car la Matrice bloque ses tirs chargés à haute énergie",
    ("dva", "hanzo"):         "D.Va bat Hanzo car la Matrice dévore ses flèches et ses Dragons de tempête",
    ("dva", "ashe"):          "D.Va plonge sur Ashe et absorbe ses tirs avec la Matrice avant qu'elle réagisse",
    ("dva", "echo"):          "D.Va chasse Echo dans les airs et la Matrice bloque ses projectiles",
    ("dva", "widowmaker"):    "D.Va dive sur Widowmaker et sa Matrice bloque le tir chargé avant l'exécution",
    # ── Winston ───────────────────────────────────────────────────────────────
    ("winston", "widowmaker"):"Winston écrase Widowmaker car il saute directement sur elle — elle ne peut pas fuir",
    ("winston", "tracer"):    "Winston domine Tracer car son tesla la suit même pendant ses Blinks",
    ("winston", "genji"):     "Winston contre Genji car son tesla inflige des dégâts continus que le deflect ne peut pas bloquer",
    ("winston", "sojourn"):   "Winston neutralise Sojourn car il dive dessus avant qu'elle charge ses tirs",
    ("winston", "hanzo"):     "Winston bat Hanzo car il saute sur lui avant qu'il puisse viser et repositionner",
    ("winston", "ashe"):      "Winston contre Ashe car il dive sur elle et l'empêche de viser depuis la distance",
    ("winston", "lucio"):     "Winston chasse Lucio car sa mobilité suit le boosteur même en patinant",
    ("winston", "baptiste"):  "Winston dive sur Baptiste et le force à utiliser ses cooldowns défensivement",
    ("winston", "mercy"):     "Winston colle Mercy au corps — elle n'a aucun outil pour s'en défaire",
    # ── Zarya ─────────────────────────────────────────────────────────────────
    ("zarya", "mei"):         "Zarya écrase Mei car la bulle protège les alliés du freeze et annule les Cryo-Congels",
    ("zarya", "cassidy"):     "Zarya contrecarre Cassidy car la bulle absorbe sa Grenade Magnétique qui colle",
    ("zarya", "genji"):       "Zarya bat Genji car la bulle absorbe ses shurikens et annule son deflect",
    ("zarya", "tracer"):      "Zarya neutralise Tracer car la bulle sauve les alliés visés par sa Pulse Bomb",
    ("zarya", "reaper"):      "Zarya résiste à Faucheur car la bulle réduit ses dégâts au corps à corps",
    ("zarya", "dva"):         "Zarya bat D.Va car le beam se charge sur la Matrice et la punit quand elle doit recharger",
    ("zarya", "winston"):     "Zarya écrase Winston car il se charge dessus et alimente son beam en permanence",
    ("zarya", "wrecking-ball"):"Zarya contre Wrecking Ball car chaque accrochage charge son beam au maximum",
    # ── Sigma ─────────────────────────────────────────────────────────────────
    ("sigma", "pharah"):      "Sigma domine Pharah car son bouclier bloque les roquettes et l'accrétion l'éjecte des airs",
    ("sigma", "bastion"):     "Sigma bat Bastion car son bouclier absorbe la rafale et il riposte à distance sûre",
    ("sigma", "ashe"):        "Sigma contre Ashe car son bouclier bloque ses tirs longue portée et la force à bouger",
    ("sigma", "hanzo"):       "Sigma neutralise Hanzo car son bouclier dévore ses flèches et ses Dragons",
    ("sigma", "soldier-76"):  "Sigma bat Soldat:76 car son bouclier bloque les rafales et l'accrétion interrompt son sprint",
    ("sigma", "echo"):        "Sigma contre Echo car l'accrétion l'éjecte en plein vol et interrompt sa copie",
    ("sigma", "widowmaker"):  "Sigma force Widowmaker à changer de position car son bouclier couvre les angles",
    ("sigma", "dva"):         "Sigma bat D.Va car l'accrétion la stun et l'ulti la sort de sa zone de confort",
    ("sigma", "junkrat"):     "Sigma absorbe toutes les grenades de Junkrat avec son bouclier sans prendre de dégâts",
    ("sigma", "mauga"):       "Sigma contre Mauga car il conteste ses HPs avec l'accrétion et le bouclier à distance",
    # ── Reinhardt ─────────────────────────────────────────────────────────────
    ("reinhardt", "bastion"):  "Reinhardt détruit Bastion car son Bouclier de Barrière absorbe toute la rafale",
    ("reinhardt", "ashe"):     "Reinhardt contre Ashe car son bouclier bloque ses tirs longs et il peut charger sur elle",
    ("reinhardt", "soldier-76"):"Reinhardt bat Soldat:76 car son bouclier bloque les rafales — au contact il n'a aucune chance",
    ("reinhardt", "cassidy"):  "Reinhardt neutralise Cassidy car le bouclier bloque ses tirs et le force au CàC où Reinhardt domine",
    ("reinhardt", "junkrat"):  "Reinhardt écrase Junkrat car le bouclier absorbe toutes ses grenades et son pneu",
    ("reinhardt", "mei"):      "Reinhardt bat Mei car le bouclier empêche le gel à distance et Fortifier lui résiste",
    ("reinhardt", "symmetra"): "Reinhardt contre Symmetra car le bouclier absorbe ses rayons et détruit ses tourelles",
    ("reinhardt", "torbjorn"):  "Reinhardt neutralise Torbjörn car le bouclier tient face à la tourelle et il charge dessus",
    ("reinhardt", "widowmaker"):"Reinhardt bat Widowmaker car son bouclier bloque le tir chargé et il peut la charger",
    ("reinhardt", "sojourn"):   "Reinhardt contre Sojourn car le bouclier bloque ses tirs chargés en droite ligne",
    # ── Orisa ─────────────────────────────────────────────────────────────────
    ("orisa", "mei"):          "Orisa bat Mei car Fortifier annule le gel — elle ne peut pas ralentir Orisa",
    ("orisa", "cassidy"):      "Orisa contre Cassidy car Fortifier réduit massivement ses dégâts par rafale",
    ("orisa", "soldier-76"):   "Orisa neutralise Soldat:76 car sa javeline interrompt son Sprint tactique",
    ("orisa", "ashe"):         "Orisa bat Ashe car sa lance la repousse et interrompt B.O.B. avant son arrivée",
    ("orisa", "roadhog"):      "Orisa contre Roadhog car elle le pull hors position avant qu'il puisse accrocher",
    ("orisa", "doomfist"):     "Orisa écrase Doomfist car elle peut l'arrêter dans son dash avec la javeline",
    ("orisa", "reinhardt"):    "Orisa contre Reinhardt car elle brise son bouclier et le pull vers son équipe",
    # ── Hazard ────────────────────────────────────────────────────────────────
    ("hazard", "venture"):     "Hazard contre Venture car il peut placer ses piques à la sortie du sol et l'intercepter",
    ("hazard", "reaper"):      "Hazard bat Faucheur car ses piques le tiennent à distance — il ne peut pas l'approcher",
    ("hazard", "cassidy"):     "Hazard contre Cassidy car sa mobilité lui permet d'esquiver le flashbang",
    ("hazard", "soldier-76"):  "Hazard neutralise Soldat:76 car il prend des angles verticaux hors de portée",
    ("hazard", "ashe"):        "Hazard bat Ashe car il peut bondir sur elle avant qu'elle vise",
    ("hazard", "widowmaker"):  "Hazard contre Widowmaker car sa mobilité rend difficile de le viser",
    ("hazard", "symmetra"):    "Hazard détruit les tourelles de Symmetra avec ses piques depuis les hauteurs",
    ("hazard", "torbjorn"):    "Hazard contre Torbjörn car il plonge sur la tourelle en hauteur",
    # ── Ramattra ──────────────────────────────────────────────────────────────
    ("ramattra", "mei"):       "Ramattra domine Mei car la forme Nemesis résiste au freeze — il s'approche sans être ralenti",
    ("ramattra", "cassidy"):   "Ramattra bat Cassidy car la forme Nemesis absorbe ses dégâts par rafale",
    ("ramattra", "reaper"):    "Ramattra contre Faucheur car la forme Nemesis réduit ses dégâts au corps à corps",
    ("ramattra", "venture"):   "Ramattra neutralise Venture car l'anneau de blocage interrompt sa sortie de terre",
    ("ramattra", "genji"):     "Ramattra contre Genji car la forme Nemesis résiste à son deflect",
    ("ramattra", "tracer"):    "Ramattra bat Tracer car l'anneau de blocage l'empêche de fuir",
    # ── Doomfist ──────────────────────────────────────────────────────────────
    ("doomfist", "zenyatta"):  "Doomfist écrase Zenyatta car il plonge directement sur lui — il n'a aucun outil de fuite",
    ("doomfist", "widowmaker"):"Doomfist bat Widowmaker car il la charge avant qu'elle vise et l'éjecte de position",
    ("doomfist", "ashe"):      "Doomfist contre Ashe car il la rush avant qu'elle monte sur B.O.B. ou vise",
    ("doomfist", "hanzo"):     "Doomfist neutralise Hanzo car il arrive sur lui avant qu'il puisse charger ses flèches",
    ("doomfist", "tracer"):    "Doomfist bat Tracer car son dash la one-shot si elle est bien ciblée",
    ("doomfist", "lucio"):     "Doomfist contre Lucio car il peut l'intercepter même en patinant grâce à sa vitesse",
    ("doomfist", "baptiste"):  "Doomfist dive sur Baptiste et force le Champ d'immortalité à l'avance",
    ("doomfist", "lifeweaver"):"Doomfist écrase Lifeweaver car il n'a aucun outil pour le stopper",
    # ── Roadhog ───────────────────────────────────────────────────────────────
    ("roadhog", "genji"):      "Roadhog bat Genji car son crochet l'attrape en plein air et le one-shot",
    ("roadhog", "tracer"):     "Roadhog contre Tracer car le crochet la ramène au corps à corps et la one-shot",
    ("roadhog", "doomfist"):   "Roadhog neutralise Doomfist car il peut l'accrocher dans son dash",
    ("roadhog", "junkrat"):    "Roadhog contre Junkrat car le crochet le ramène au corps à corps — sa portée disparaît",
    ("roadhog", "cassidy"):    "Roadhog bat Cassidy car le crochet ignore son flashbang et le one-shot",
    ("roadhog", "bastion"):    "Roadhog accroche Bastion et le one-shot hors de sa position défensive",
    ("roadhog", "ashe"):       "Roadhog attrape Ashe avec le crochet avant qu'elle monte sur B.O.B.",
    ("roadhog", "reinhardt"):  "Roadhog contre Reinhardt car le crochet le tire hors de son bouclier",
    # ── Junker Queen ──────────────────────────────────────────────────────────
    ("junker-queen", "moira"):  "Junker Queen contre Moira car ses blessures empêchent les soins — Moira se soigne moins",
    ("junker-queen", "lifeweaver"):"Junker Queen bat Lifeweaver car ses blessures réduisent ses soins à presque zéro",
    ("junker-queen", "tracer"): "Junker Queen contre Tracer car la hache applique des blessures permanentes",
    ("junker-queen", "genji"):  "Junker Queen bat Genji car ses blessures s'appliquent même si il deflect",
    ("junker-queen", "reaper"): "Junker Queen contre Faucheur car les blessures annulent son vol d'âme",
    # ── Mauga ─────────────────────────────────────────────────────────────────
    ("mauga", "genji"):         "Mauga contre Genji car ses mitrailleuses infligent des dégâts continus malgré le deflect",
    ("mauga", "tracer"):        "Mauga bat Tracer car ses doubles mitrailleuses la punissent même en mouvement",
    ("mauga", "soldier-76"):    "Mauga domine Soldat:76 à mi-portée car son volume de feu l'écrase",
    ("mauga", "pharah"):        "Mauga contre Pharah car sa mitrailleuse incendiaire la detruit rapidement dans les airs",
    ("mauga", "widowmaker"):    "Mauga bat Widowmaker car son HPs massif encaisse les tirs chargés",
    # ── Wrecking Ball ─────────────────────────────────────────────────────────
    ("wrecking-ball", "zenyatta"):  "Wrecking Ball écrase Zenyatta car il arrive trop vite pour qu'il réagisse",
    ("wrecking-ball", "widowmaker"):"Wrecking Ball contre Widowmaker car il la déplace constamment avec ses lancers",
    ("wrecking-ball", "tracer"):    "Wrecking Ball bat Tracer car son pilon la one-shot si elle est mal positionnée",
    ("wrecking-ball", "ana"):       "Wrecking Ball neutralise Ana car il l'approche trop vite pour qu'elle vise",
    ("wrecking-ball", "ashe"):      "Wrecking Ball contre Ashe car il perturbe son positionnement en continu",
    ("wrecking-ball", "lucio"):     "Wrecking Ball bat Lucio car il peut le suivre et le pilon le one-shot",
    ("wrecking-ball", "mercy"):     "Wrecking Ball colle Mercy — elle ne peut pas fuir ses lancers",

    # ── Cassidy ───────────────────────────────────────────────────────────────
    ("cassidy", "genji"):      "Cassidy bat Genji car son flashbang l'étourdit en plein deflect et le one-shot",
    ("cassidy", "tracer"):     "Cassidy contre Tracer car le flashbang annule ses Blinks et la one-shot",
    ("cassidy", "dva"):        "Cassidy bat D.Va car la Grenade Magnétique colle à la Matrice et force les dégâts",
    ("cassidy", "winston"):    "Cassidy contre Winston car chaque rafale après le flashbang le détruit rapidement",
    ("cassidy", "wrecking-ball"):"Cassidy bat Wrecking Ball car le flashbang l'immobilise dans ses lancers",
    ("cassidy", "roadhog"):    "Cassidy bat Roadhog car le flashbang interrompt son crochet",
    ("cassidy", "pharah"):     "Cassidy contre Pharah avec son grenade magnétique en l'air",
    # ── Genji ─────────────────────────────────────────────────────────────────
    ("genji", "zenyatta"):     "Genji domine Zenyatta car il dive directement sur lui — zéro outil de fuite",
    ("genji", "ana"):          "Genji contre Ana car il peut deflect ses fléchettes et se soigner",
    ("genji", "mercy"):        "Genji colle Mercy — elle ne peut pas voler assez vite pour lui échapper",
    ("genji", "bastion"):      "Genji contre Bastion car deflect renvoie toute sa rafale en mode Artillerie",
    ("genji", "lucio"):        "Genji chase Lucio car sa mobilité verticale suit le boosteur",
    ("genji", "lifeweaver"):   "Genji écrase Lifeweaver car il n'a aucun outil pour le contester",
    ("genji", "baptiste"):     "Genji dive Baptiste et le force à utiliser ses cooldowns défensivement",
    # ── Tracer ────────────────────────────────────────────────────────────────
    ("tracer", "zenyatta"):    "Tracer domine Zenyatta car elle arrive trop vite et il n'a aucun escape",
    ("tracer", "ana"):         "Tracer contre Ana car elle peut rembobiner après une fléchette soporifique",
    ("tracer", "widowmaker"):  "Tracer bat Widowmaker car elle arrive dessus avant qu'elle vise — elle ne peut pas fuir",
    ("tracer", "ashe"):        "Tracer contre Ashe car elle est trop rapide pour être ciblée par ses tirs longs",
    ("tracer", "hanzo"):       "Tracer neutralise Hanzo car elle est trop mobile pour ses flèches chargées",
    ("tracer", "bastion"):     "Tracer plante sa Pulse Bomb sur Bastion en mode Artillerie et recule",
    ("tracer", "illari"):      "Tracer contre Illari car elle dive dessus avant qu'elle place son Soleil captif",
    ("tracer", "baptiste"):    "Tracer colle Baptiste et force ses cooldowns défensivement",
    # ── Reaper ────────────────────────────────────────────────────────────────
    ("reaper", "reinhardt"):   "Faucheur écrase Reinhardt car au corps à corps ses deux fusils le détruisent",
    ("reaper", "roadhog"):     "Faucheur bat Roadhog car il vol d'âme toute tentative de self-soin",
    ("reaper", "orisa"):       "Faucheur domine Orisa au corps à corps — Fortifier ne suffit pas contre deux fusils à bout portant",
    ("reaper", "sigma"):       "Faucheur contre Sigma car il rentre au corps à corps où le bouclier ne sert à rien",
    ("reaper", "wrecking-ball"):"Faucheur bat Wrecking Ball car il Téléporte directement au contact",
    ("reaper", "winston"):     "Faucheur écrase Winston car son tesla ne fait pas assez de dégâts comparé aux deux fusils",
    ("reaper", "mauga"):       "Faucheur contre Mauga car le vol d'âme compense les dégâts massifs",
    ("reaper", "doomfist"):    "Faucheur bat Doomfist car au corps à corps ses fusils font plus de dégâts",
    # ── Sombra ────────────────────────────────────────────────────────────────
    ("sombra", "doomfist"):    "Sombra contre Doomfist car le hack désactive tous ses skills de mobilité",
    ("sombra", "wrecking-ball"):"Sombra écrase Wrecking Ball car le hack le force hors de sa forme rouleau",
    ("sombra", "roadhog"):     "Sombra bat Roadhog car le hack annule son self-soin — il devient une cible facile",
    ("sombra", "bastion"):     "Sombra contre Bastion car le hack le sort de la forme Artillerie",
    ("sombra", "lucio"):       "Sombra neutralise Lucio car le hack coupe son boost de vitesse et ses soins",
    ("sombra", "pharah"):      "Sombra bat Pharah car le hack la fait tomber du ciel instantanément",
    ("sombra", "dva"):         "Sombra hack D.Va et lui retire la Matrice — elle ne peut plus bloquer",
    ("sombra", "winston"):     "Sombra contre Winston car le hack coupe son saut et son tesla",
    ("sombra", "mauga"):       "Sombra bat Mauga car le hack annule sa résistance et expose ses faiblesses",
    ("sombra", "ana"):         "Sombra contre Ana car le hack l'empêche d'utiliser ses grenades et fléchettes",
    ("sombra", "orisa"):       "Sombra bat Orisa car le hack annule Fortifier et la javeline",
    ("sombra", "reinhardt"):   "Sombra contre Reinhardt car le hack désactive son bouclier au pire moment",
    # ── Mei ───────────────────────────────────────────────────────────────────
    ("mei", "tracer"):         "Mei contre Tracer car le souffle de glace la gèle avant qu'elle Blink assez vite",
    ("mei", "genji"):          "Mei bat Genji car le gel annule ses déflexions et sa fuite",
    ("mei", "doomfist"):       "Mei contre Doomfist car le gel annule son dash en plein élan",
    ("mei", "winston"):        "Mei bat Winston car elle le gèle à distance — il ne peut pas sauter dessus",
    ("mei", "wrecking-ball"):  "Mei contre Wrecking Ball car les murs bloquent ses lancers et le gel l'immobilise",
    ("mei", "venture"):        "Mei bat Venture car elle peut le geler à la sortie de son terrier",
    ("mei", "dva"):            "Mei contre D.Va car le gel l'immobilise et elle ne peut pas Matrice en étant congelée",
    # ── Sojourn ───────────────────────────────────────────────────────────────
    ("sojourn", "reinhardt"):  "Sojourn contre Reinhardt car son tir chargé perce son bouclier",
    ("sojourn", "orisa"):      "Sojourn bat Orisa car ses tirs chargés infligent d'énormes dégâts à travers Fortifier",
    ("sojourn", "sigma"):      "Sojourn contre Sigma car son tir chargé traverse son bouclier",
    ("sojourn", "zenyatta"):   "Sojourn one-shot Zenyatta avec un seul tir chargé — il n'a aucune armure",
    ("sojourn", "ana"):        "Sojourn bat Ana car elle la one-shot avant qu'elle puisse réagir",
    ("sojourn", "mercy"):      "Sojourn contre Mercy car son tir chargé la one-shot avant qu'elle vole",
    ("sojourn", "widowmaker"): "Sojourn bat Widowmaker au duel car sa glissade rend difficile de la viser",
    # ── Widowmaker ────────────────────────────────────────────────────────────
    ("widowmaker", "zenyatta"):"Widowmaker one-shot Zenyatta à chaque rechargement — il n'a aucune armure",
    ("widowmaker", "ana"):     "Widowmaker bat Ana au duel longue portée car son tir chargé la one-shot",
    ("widowmaker", "mercy"):   "Widowmaker contre Mercy car elle la one-shot même en plein vol",
    ("widowmaker", "bastion"): "Widowmaker bat Bastion car son tir chargé ignore sa grande hitbox facilement",
    ("widowmaker", "reinhardt"):"Widowmaker contre Reinhardt car son tir perce son bouclier par les bords",
    ("widowmaker", "sigma"):   "Widowmaker bat Sigma car elle vise par dessus son bouclier depuis les hauteurs",
    ("widowmaker", "soldier-76"):"Widowmaker domine Soldat:76 à longue portée — sa portée est illimitée",
    # ── Pharah ────────────────────────────────────────────────────────────────
    ("pharah", "reinhardt"):   "Pharah domine Reinhardt car ses roquettes explosent derrière son bouclier",
    ("pharah", "bastion"):     "Pharah contre Bastion car elle bombarde d'en haut hors de sa portée",
    ("pharah", "torbjorn"):    "Pharah neutralise Torbjörn car la tourelle ne peut pas viser assez haut",
    ("pharah", "symmetra"):    "Pharah bat Symmetra car ses tourelles ne l'atteignent pas dans les airs",
    ("pharah", "junkrat"):     "Pharah contre Junkrat car elle bombarbe son pack depuis les airs",
    # ── Soldier:76 ────────────────────────────────────────────────────────────
    ("soldier-76", "zenyatta"):"Soldat:76 détruit Zenyatta car ses rafales précises le tuent avant qu'il riposte",
    ("soldier-76", "bastion"): "Soldat:76 contre Bastion car le sprint lui permet de flanquer hors de la zone de feu",
    ("soldier-76", "torbjorn"):"Soldat:76 bat Torbjörn car la précision de son spray détruit la tourelle à distance",
    ("soldier-76", "reinhardt"):"Soldat:76 contre Reinhardt car le sprint permet de jouer les angles et de flanquer",
    ("soldier-76", "orisa"):   "Soldat:76 bat Orisa car la précision de ses tirs punit ses déplacements lents",
    ("soldier-76", "sigma"):   "Soldat:76 contre Sigma car le sprint lui permet de contourner son bouclier",
    # ── Hanzo ─────────────────────────────────────────────────────────────────
    ("hanzo", "reinhardt"):    "Hanzo contre Reinhardt car sa flèche de dispersion pénètre sous le bouclier",
    ("hanzo", "sigma"):        "Hanzo bat Sigma car ses Dragons passent à travers son bouclier",
    ("hanzo", "bastion"):      "Hanzo contre Bastion car ses flèches pénétrantes ignorent son armure",
    ("hanzo", "orisa"):        "Hanzo bat Orisa car ses flèches font de gros dégâts à travers Fortifier",
    ("hanzo", "zenyatta"):     "Hanzo one-shot Zenyatta à pleine charge — aucune armure ne protège",
    # ── Symmetra ──────────────────────────────────────────────────────────────
    ("symmetra", "reinhardt"): "Symmetra contre Reinhardt car ses tourelles déchargent derrière son bouclier",
    ("symmetra", "bastion"):   "Symmetra contre Bastion car ses tourelles cumulées détruisent sa résistance",
    ("symmetra", "orisa"):     "Symmetra bat Orisa car son rayon se charge sur les gros HPs et la détruit",
    ("symmetra", "ramattra"):  "Symmetra contre Ramattra car ses tourelles l'arrosent même en forme Nemesis",
    # ── Junkrat ───────────────────────────────────────────────────────────────
    ("junkrat", "reinhardt"):  "Junkrat bat Reinhardt car ses grenades rebondissent derrière son bouclier",
    ("junkrat", "bastion"):    "Junkrat contre Bastion car son pneu contourne ses angles défensifs",
    ("junkrat", "orisa"):      "Junkrat bat Orisa car ses grenades rebondissent sur Fortifier",
    ("junkrat", "torbjorn"):   "Junkrat neutralise Torbjörn car son pneu détruit la tourelle sans risque",
    ("junkrat", "symmetra"):   "Junkrat bat Symmetra car son pneu détruit toutes ses tourelles d'un coup",
    ("junkrat", "sigma"):      "Junkrat contre Sigma car ses grenades rebondissent autour du bouclier",
    # ── Bastion ───────────────────────────────────────────────────────────────
    ("bastion", "reinhardt"):  "Bastion détruit le bouclier de Reinhardt en quelques secondes en mode Artillerie",
    ("bastion", "orisa"):      "Bastion bat Orisa car sa rafale ignore Fortifier avec son volume de feu",
    ("bastion", "ramattra"):   "Bastion contre Ramattra car même la forme Nemesis ne tient pas sous la rafale",
    ("bastion", "sigma"):      "Bastion bat Sigma car sa rafale brise son bouclier en quelques secondes",
    # ── Echo ──────────────────────────────────────────────────────────────────
    ("echo", "reinhardt"):     "Echo bat Reinhardt car sa mobilité lui permet de flanquer et ses orbes infligent beaucoup de dégâts",
    ("echo", "sigma"):         "Echo contre Sigma car elle vole hors de portée de son bouclier et accrétion",
    ("echo", "bastion"):       "Echo bat Bastion car elle peut le copier et utiliser sa puissance contre lui",
    ("echo", "orisa"):         "Echo contre Orisa en la ciblant depuis les airs hors de portée",
    # ── Venture ───────────────────────────────────────────────────────────────
    ("venture", "zenyatta"):   "Venture dive sous terre puis sort sur Zenyatta — aucun escape possible",
    ("venture", "ana"):        "Venture contre Ana car il sort du sol trop vite pour qu'elle fléchette",
    ("venture", "mercy"):      "Venture bat Mercy car il peut la cibler depuis sous terre",
    ("venture", "lifeweaver"): "Venture contre Lifeweaver car il sort du sol directement sur lui",
    ("venture", "bastion"):    "Venture bat Bastion car il sort du sol derrière lui en surprise",
    ("venture", "torbjorn"):   "Venture détruit la tourelle de Torbjörn en passant sous terre",
    ("venture", "reinhardt"):  "Venture contre Reinhardt car il peut contourner son bouclier par le bas",
    # ── Emre (DPS mobile) ─────────────────────────────────────────────────────
    ("emre", "tracer"):        "Emre contre Tracer car ses capacités de fuite lui permettent de survivre",
    ("emre", "genji"):         "Emre bat Genji car il peut esquiver ses attaques et riposter efficacement",
    ("emre", "zenyatta"):      "Emre dive sur Zenyatta — il n'a aucun outil de fuite",
    ("emre", "widowmaker"):    "Emre contre Widowmaker car sa mobilité le rend difficile à viser",

    # ── Ana ────────────────────────────────────────────────────────────────────
    ("ana", "sojourn"):        "Ana contre Sojourn car la fléchette soporifique l'empêche de charger sa glissade",
    ("ana", "widowmaker"):     "Ana bat Widowmaker au duel car elle l'endort avant qu'elle vise",
    ("ana", "bastion"):        "Ana contre Bastion car l'anti-soin annule ses soins passifs en forme Artillerie",
    ("ana", "ashe"):           "Ana bat Ashe car la grenade anti-soin empêche toute récupération après un duel",
    ("ana", "soldier-76"):     "Ana contre Soldat:76 car sa grenade annule son Biotic Field sur le sol",
    ("ana", "hanzo"):          "Ana bat Hanzo car la fléchette soporifique interrompt sa concentration à longue portée",
    ("ana", "venture"):        "Ana contre Venture car la fléchette l'endort à sa sortie de terrier",
    ("ana", "junkrat"):        "Ana bat Junkrat car l'anti-soin l'empêche de se soigner entre les duels",
    ("ana", "roadhog"):        "Ana contre Roadhog car l'anti-soin annule totalement son self-soin",
    ("ana", "mauga"):          "Ana écrase Mauga car sans soins ses HPs fondent rapidement",
    ("ana", "junker-queen"):   "Ana contre Junker Queen car la grenade annule ses blessures auto-soignantes",
    ("ana", "wrecking-ball"):  "Ana bat Wrecking Ball car la fléchette le force à sortir de sa forme rouleau",
    ("ana", "winston"):        "Ana contre Winston car elle l'endort en plein saut",
    ("ana", "reaper"):         "Ana bat Faucheur car l'anti-soin supprime son vol d'âme — il ne récupère plus rien",
    ("ana", "moira"):          "Ana contre Moira car l'anti-soin annule ses orbes de soin",
    # ── Baptiste ──────────────────────────────────────────────────────────────
    ("baptiste", "bastion"):   "Baptiste bat Bastion car le Champ d'immortalité permet à l'équipe de survivre à toute sa rafale",
    ("baptiste", "sojourn"):   "Baptiste contre Sojourn car le Champ d'immortalité annule ses one-shots chargés",
    ("baptiste", "torbjorn"):  "Baptiste neutralise Torbjörn car sa lampe de soin détruit facilement la tourelle",
    ("baptiste", "soldier-76"):"Baptiste bat Soldat:76 à mi-portée car son tir en rafale domaine sa précision",
    ("baptiste", "ashe"):      "Baptiste contre Ashe car le Champ d'immortalité annule ses picks depuis la distance",
    ("baptiste", "junkrat"):   "Baptiste bat Junkrat car le Champ d'immortalité absorbe ses combos en pneu",
    ("baptiste", "orisa"):     "Baptiste contre Orisa car son Champ force à casser la phase offensive",
    ("baptiste", "pharah"):    "Baptiste bat Pharah car son tir en arc de cercle la punit dans les airs",
    ("baptiste", "roadhog"):   "Baptiste contre Roadhog car la lampe retire le bénéfice de son self-soin",
    # ── Kiriko ────────────────────────────────────────────────────────────────
    ("kiriko", "mei"):         "Kiriko bat Mei car Suzu nettoie instantanément le gel sur tous les alliés",
    ("kiriko", "sombra"):      "Kiriko contre Sombra car Suzu supprime son hack — les alliés hackés retrouvent leurs skills",
    ("kiriko", "cassidy"):     "Kiriko bat Cassidy car Suzu supprime sa Grenade Magnétique avant l'explosion",
    ("kiriko", "soldier-76"):  "Kiriko contre Soldat:76 car elle peut téléporter ses alliés hors de son ulti",
    ("kiriko", "sojourn"):     "Kiriko bat Sojourn car Suzu cleanse les effets de ralentissement",
    ("kiriko", "venture"):     "Kiriko contre Venture car Suzu nettoie les effets de sa sortie du sol",
    ("kiriko", "widowmaker"):  "Kiriko bat Widowmaker car Suzu protège les alliés visés juste avant le tir",
    ("kiriko", "ana"):         "Kiriko contre Ana car Suzu nettoie la fléchette soporifique et l'anti-soin",
    ("kiriko", "doomfist"):    "Kiriko bat Doomfist car Suzu protège les alliés de son combo",
    ("kiriko", "roadhog"):     "Kiriko contre Roadhog car Suzu annule son crochet sur les alliés",
    # ── Zenyatta ──────────────────────────────────────────────────────────────
    ("zenyatta", "bastion"):   "Zenyatta contre Bastion car l'Orbe de discorde double les dégâts reçus",
    ("zenyatta", "widowmaker"):"Zenyatta bat Widowmaker car l'Orbe de discorde force toute l'équipe à la cibler",
    ("zenyatta", "cassidy"):   "Zenyatta contre Cassidy car l'Orbe de discorde compense son armure lourde",
    ("zenyatta", "ashe"):      "Zenyatta bat Ashe car l'Orbe de discorde rend sa longue portée moins dominante",
    ("zenyatta", "hanzo"):     "Zenyatta contre Hanzo car l'Orbe de discorde amplifie chaque flèche reçue",
    ("zenyatta", "soldier-76"):"Zenyatta bat Soldat:76 car l'Orbe de discorde le détruit rapidement en rafales",
    ("zenyatta", "junkrat"):   "Zenyatta contre Junkrat car Transcendance permet à l'équipe de survivre à son ulti",
    ("zenyatta", "roadhog"):   "Zenyatta bat Roadhog car l'Orbe de discorde amplifie tous les tirs sur lui",
    ("zenyatta", "dva"):       "Zenyatta contre D.Va car l'Orbe de discorde punit chaque rechargement de Matrice",
    ("zenyatta", "mauga"):     "Zenyatta bat Mauga car l'Orbe de discorde accélère sa destruction",
    ("zenyatta", "reinhardt"): "Zenyatta contre Reinhardt car l'Orbe de discorde force à détruire son bouclier plus vite",
    ("zenyatta", "orisa"):     "Zenyatta bat Orisa car l'Orbe de discorde punit Fortifier",
    ("zenyatta", "tracer"):    "Zenyatta contre Tracer car l'Orbe de discorde la rend vulnérable à un seul tir",
    ("zenyatta", "genji"):     "Zenyatta bat Genji car l'Orbe de discorde amplifie chaque coup au contact",
    ("zenyatta", "sombra"):    "Zenyatta contre Sombra car l'Orbe de discorde la condamne si elle approche",
    # ── Brigitte ──────────────────────────────────────────────────────────────
    ("brigitte", "tracer"):    "Brigitte écrase Tracer car le Coup de bouclier l'étourdit en plein Blink",
    ("brigitte", "genji"):     "Brigitte bat Genji car le Coup de bouclier l'étourdit en plein deflect",
    ("brigitte", "sombra"):    "Brigitte contre Sombra car son armure passive l'empêche d'être one-shot hackée",
    ("brigitte", "reaper"):    "Brigitte bat Faucheur car le coup l'éloigne et ses packs d'armure réduisent ses dégâts",
    ("brigitte", "echo"):      "Brigitte contre Echo car son fléau interrompt son vol et son bouclier la gène",
    ("brigitte", "doomfist"):  "Brigitte bat Doomfist car son stun interrompt son dash",
    ("brigitte", "pharah"):    "Brigitte contre Pharah car son fléau la repousse hors position",
    ("brigitte", "dva"):       "Brigitte bat D.Va car son bouclier résiste à la Matrice",
    ("brigitte", "venture"):   "Brigitte contre Venture car le Coup de bouclier l'étourdit à la sortie de terre",
    ("brigitte", "mei"):       "Brigitte bat Mei car les packs d'armure protègent l'équipe du gel",
    ("brigitte", "ashe"):      "Brigitte contre Ashe car son fléau la repousse hors de sa position longue portée",
    ("brigitte", "cassidy"):   "Brigitte bat Cassidy car son stun interrompt son flashbang",
    # ── Lucio ─────────────────────────────────────────────────────────────────
    ("lucio", "widowmaker"):   "Lucio contre Widowmaker car le boost de vitesse permet à l'équipe d'éviter ses lignes de mire",
    ("lucio", "symmetra"):     "Lucio bat Symmetra car la vitesse de groupe annule l'utilité de ses tourelles",
    ("lucio", "torbjorn"):     "Lucio contre Torbjörn car le boost de vitesse permet de rusher et détruire la tourelle",
    ("lucio", "pharah"):       "Lucio contre Pharah car le Boop envoie Pharah hors de sa zone de confort",
    ("lucio", "bastion"):      "Lucio bat Bastion car la vitesse permet d'approcher en sécurité hors de sa zone",
    ("lucio", "reinhardt"):    "Lucio contre Reinhardt car la vitesse empêche sa charge et ses alliés esquivent",
    ("lucio", "orisa"):        "Lucio bat Orisa car la vitesse permet d'esquiver sa javeline",
    ("lucio", "roadhog"):      "Lucio contre Roadhog car la vitesse rend difficile d'attraper les alliés au crochet",
    ("lucio", "doomfist"):     "Lucio bat Doomfist car la vitesse éloigne l'équipe de son combo",
    ("lucio", "sombra"):       "Lucio contre Sombra car son aura de vitesse rend ses alliés plus difficiles à hacker",
    # ── Moira ─────────────────────────────────────────────────────────────────
    ("moira", "reaper"):       "Moira bat Faucheur car Fade annule sa téléportation et esquive tous ses dégâts",
    ("moira", "venture"):      "Moira contre Venture car Fade passe à travers toutes ses attaques de sortie",
    ("moira", "mei"):          "Moira bat Mei car Fade annule le gel et se nettoie des effets",
    ("moira", "tracer"):       "Moira contre Tracer car sa sphère de dégâts la suit même en Blink",
    ("moira", "ana"):          "Moira bat Ana car Fade annule sa fléchette soporifique",
    ("moira", "sigma"):        "Moira contre Sigma car son orbe passe à travers son bouclier",
    ("moira", "sombra"):       "Moira bat Sombra car Fade annule son hack au moment critique",
    ("moira", "genji"):        "Moira contre Genji car son orbe le suit même pendant ses dash",
    ("moira", "junker-queen"): "Moira bat Junker Queen car ses soins dépassent les blessures de JQ",
    # ── Mercy ─────────────────────────────────────────────────────────────────
    ("mercy", "pharah"):       "Mercy contre Pharah car l'amplification de dégâts transforme un DPS en anti-air",
    ("mercy", "echo"):         "Mercy bat Echo car sa résurrection empêche la copie ennemie de durer",
    ("mercy", "widowmaker"):   "Mercy contre Widowmaker car boost + résurrection annule ses picks un par un",
    ("mercy", "bastion"):      "Mercy amplifie les dégâts d'un allié sur Bastion et le détruit vite",
    ("mercy", "hanzo"):        "Mercy avec boost de dégâts permet de one-shot à la place de Hanzo",
    ("mercy", "sojourn"):      "Mercy contrecarre Sojourn car la résurrection annule ses one-shots",
    ("mercy", "reaper"):       "Mercy bat Faucheur car résurrection annule ses picks au corps à corps",
    # ── Illari ────────────────────────────────────────────────────────────────
    ("illari", "pharah"):      "Illari contre Pharah car son Soleil captif la cible automatiquement dans les airs",
    ("illari", "dva"):         "Illari bat D.Va car son tir perce la Matrice depuis les hauteurs",
    ("illari", "reinhardt"):   "Illari contre Reinhardt car elle tire depuis la hauteur et contourne son bouclier",
    ("illari", "genji"):       "Illari bat Genji car son Soleil captif le cible même en plein dash",
    ("illari", "tracer"):      "Illari contre Tracer car son Soleil la suit partout",
    ("illari", "wrecking-ball"):"Illari bat Wrecking Ball car son Soleil captif le cible pendant ses rotations",
    ("illari", "widowmaker"):  "Illari contre Widowmaker car elle tire depuis la même hauteur et domine le duel",
    ("illari", "bastion"):     "Illari bat Bastion car son tir perce depuis les angles en hauteur",
    ("illari", "sojourn"):     "Illari contre Sojourn car son Soleil captif la suit pendant sa glissade",
    # ── Juno ──────────────────────────────────────────────────────────────────
    ("juno", "pharah"):        "Juno contre Pharah car elle peut la suivre dans les airs et riposter",
    ("juno", "dva"):           "Juno bat D.Va car sa mobilité lui permet d'esquiver la Matrice",
    ("juno", "mauga"):         "Juno contre Mauga car son boost de vitesse sort l'équipe de son Cage Thoracique",
    ("juno", "orisa"):         "Juno bat Orisa car son accélération permet d'éviter la javeline",
    ("juno", "roadhog"):       "Juno contre Roadhog car la vitesse rend ses alliés difficiles à accrocher",
    ("juno", "widowmaker"):    "Juno bat Widowmaker car ses orbes de soin neutralisent ses picks",
    ("juno", "soldier-76"):    "Juno contre Soldat:76 car son boost permet d'esquiver son Ultime Tactique",
    # ── Lifeweaver ────────────────────────────────────────────────────────────
    ("lifeweaver", "roadhog"):  "Lifeweaver contre Roadhog car il sauve les alliés crochétés avec son traction",
    ("lifeweaver", "doomfist"): "Lifeweaver bat Doomfist car il déplace les alliés hors de portée de son combo",
    ("lifeweaver", "genji"):    "Lifeweaver contre Genji car il repositionne les alliés visés",
    ("lifeweaver", "tracer"):   "Lifeweaver bat Tracer car sa plateforme de soin repositionne les alliés visés",
    ("lifeweaver", "pharah"):   "Lifeweaver contre Pharah car il tire et soigne depuis les hauteurs",
    ("lifeweaver", "sombra"):   "Lifeweaver bat Sombra car il peut repositionner les alliés hackés",
    ("lifeweaver", "sojourn"):  "Lifeweaver contre Sojourn car il sauve les alliés one-shotés avec la résurrection",
    ("lifeweaver", "ashe"):     "Lifeweaver bat Ashe car il repositionne ses alliés hors des lignes de mire",
    # ── Mizuki ────────────────────────────────────────────────────────────────
    ("mizuki", "roadhog"):     "Mizuki contre Roadhog car ses soins permettent à l'équipe de tenir son agression",
    ("mizuki", "mauga"):       "Mizuki bat Mauga car ses soins constants compensent son volume de feu",
    ("mizuki", "orisa"):       "Mizuki contre Orisa car ses soins et utilitaires maintiennent l'équipe en vie",
    ("mizuki", "reinhardt"):   "Mizuki bat Reinhardt car elle soigne l'équipe pendant les poussées",
    ("mizuki", "tracer"):      "Mizuki contre Tracer car ses soins rapides sauvent les alliés visés",
    ("mizuki", "genji"):       "Mizuki bat Genji car elle peut soigner ses alliés plus vite qu'il ne les tue",
    ("mizuki", "wrecking-ball"):"Mizuki contre Wrecking Ball car ses soins tiennent l'équipe pendant ses disruptions",
    # ── Wuyang ────────────────────────────────────────────────────────────────
    ("wuyang", "genji"):       "Wuyang contre Genji car ses utilitaires protègent les alliés de ses assauts",
    ("wuyang", "tracer"):      "Wuyang bat Tracer car ses soins rapides sauvent les alliés visés",
    ("wuyang", "sombra"):      "Wuyang contre Sombra car ses capacités maintiennent les alliés hackés en vie",
    ("wuyang", "roadhog"):     "Wuyang bat Roadhog car ses soins compensent son agression de crochet",
    ("wuyang", "widowmaker"):  "Wuyang contre Widowmaker car ses soins annulent ses picks un par un",
    # ── Jetpack Cat ───────────────────────────────────────────────────────────
    ("jetpack-cat", "genji"):  "Jetpack Cat contre Genji car sa mobilité aérienne lui permet de fuir ses assauts",
    ("jetpack-cat", "tracer"): "Jetpack Cat bat Tracer car il peut soigner rapidement les alliés visés",
    ("jetpack-cat", "sombra"): "Jetpack Cat contre Sombra car il maintient les alliés hackés en vie",
    ("jetpack-cat", "roadhog"):"Jetpack Cat bat Roadhog car ses soins compensent ses crochets",
    # ── Freja ─────────────────────────────────────────────────────────────────
    ("freja", "zenyatta"):     "Freja bat Zenyatta car elle dive sur lui — aucun escape possible",
    ("freja", "widowmaker"):   "Freja contre Widowmaker car sa mobilité rend sa visée difficile",
    ("freja", "ana"):          "Freja bat Ana car elle peut l'approcher rapidement",
    ("freja", "mercy"):        "Freja contre Mercy car sa mobilité lui permet de la suivre en vol",
    ("freja", "lucio"):        "Freja bat Lucio car elle peut le chasser grâce à sa mobilité",
    ("freja", "torbjorn"):     "Freja contre Torbjörn car elle plonge sur lui avant qu'il place sa tourelle",
    ("freja", "bastion"):      "Freja bat Bastion car elle peut flanquer depuis les hauteurs",
    # ── Sierra ────────────────────────────────────────────────────────────────
    ("sierra", "zenyatta"):    "Sierra bat Zenyatta car elle peut le cibler efficacement",
    ("sierra", "widowmaker"):  "Sierra contre Widowmaker car elle perturbe son positionnement",
    ("sierra", "ana"):         "Sierra bat Ana car elle peut l'approcher rapidement",
    ("sierra", "bastion"):     "Sierra contre Bastion car elle flanque depuis les angles",
    ("sierra", "torbjorn"):    "Sierra bat Torbjörn car elle détruit sa tourelle rapidement",
    # ── Vendetta ──────────────────────────────────────────────────────────────
    ("vendetta", "zenyatta"):  "Vendetta bat Zenyatta car il n'a aucune défense contre un flanqueur",
    ("vendetta", "widowmaker"):"Vendetta contre Widowmaker car il perturbe son positionnement longue portée",
    ("vendetta", "ana"):       "Vendetta bat Ana car il l'approche trop vite pour qu'elle réagisse",
    ("vendetta", "reinhardt"): "Vendetta contre Reinhardt car il peut contourner son bouclier",
    ("vendetta", "bastion"):   "Vendetta bat Bastion car il flanque hors de sa zone de feu",
    ("vendetta", "sigma"):     "Vendetta contre Sigma car il passe ses boucliers par les flancs",
    ("vendetta", "mercy"):     "Vendetta bat Mercy car elle ne peut pas fuir un flanqueur mobile",
    ("vendetta", "lifeweaver"):"Vendetta contre Lifeweaver car il n'a aucun outil offensif pour le stopper",

    # ── Domina (tank agressif, haute pression frontale) ────────────────────────
    ("domina", "ashe"):        "Domina s'avance sur Ashe en absorbant ses tirs — force-la à reculer et à quitter sa position longue portée. Joue agressif pour couper sa ligne de mire.",
    ("domina", "soldier-76"):  "Domina rentre au contact de Soldat:76 où ses rafales sont moins efficaces. Pousse directement sur lui — il n'a pas d'outil pour te repousser au CàC.",
    ("domina", "hanzo"):       "Domina s'avance sur Hanzo en ligne droite — il ne peut pas charger ses flèches si tu es sur lui. Pousse tôt, force-le à se repositionner constamment.",
    ("domina", "cassidy"):     "Domina entre au CàC avec Cassidy avant qu'il flashbang. Reste mobile et approche depuis un angle — son flashbang ne porte qu'à courte portée.",
    ("domina", "sojourn"):     "Domina absorbe les premiers tirs de Sojourn et rush sur elle. Sa glissade est défensive — si tu es déjà sur elle elle ne peut pas s'échapper facilement.",
    ("domina", "widowmaker"):  "Domina monte sur Widowmaker dès qu'elle se montre. Son tir chargé met du temps — si tu es sur elle avant qu'elle vise tu gagnes le duel.",
    ("domina", "pharah"):      "Domina utilise ses projectiles longue portée pour pression Pharah dans les airs. Force-la à redescendre ou à gaspiller ses roquettes à grande distance.",
    ("domina", "echo"):        "Domina punit Echo quand elle reste statique pour attaquer. Pousse sur elle dès qu'elle est au sol — dans les airs elle est difficile à cibler.",
    ("domina", "reaper"):      "Domina contre Faucheur en maintenant la distance. Joue en dehors de sa portée effective — ses fusils sont inefficaces au-delà de 10m.",
    ("domina", "sombra"):      "Domina maintient sa pression même si hackée — ses capacités de base restent opérationnelles. Reste proactive et ne laisse pas Sombra dicter le rythme.",
    ("domina", "tracer"):      "Domina ignore Tracer et focus les cibles à haute valeur. Ses HP massifs encaissent les dégâts de Tracer — laisse tes supports la gérer.",
    ("domina", "genji"):       "Domina punit Genji quand il dive sur ta backline. Tourne-toi vers lui dès qu'il engage — son deflect ne marche pas contre les gros projectiles.",
    ("domina", "venture"):     "Domina place sa pression de zone là où Venture va sortir. Anticipe sa sortie de terrier et positionne-toi pour le punir dès qu'il émerge.",
    ("domina", "anran"):       "Domina absorbe les dégâts d'Anran et force son repositionnement. Avance constamment — Anran perd son efficacité si tu es sur lui.",
    ("domina", "junkrat"):     "Domina s'approche de Junkrat pour invalider ses grenades en arc. Au CàC ses grenades lui font autant de dégâts à lui qu'à toi.",

    # ── Hazard (tank mobile, contrôle vertical) ────────────────────────────────
    ("hazard", "hanzo"):       "Hazard monte sur les hauteurs pour flanquer Hanzo depuis son propre angle. Hazard prend les positions verticales avant lui — il ne peut pas viser en bas efficacement.",
    ("hazard", "junkrat"):     "Hazard plonge sur Junkrat depuis les airs où ses grenades en arc ne peuvent pas te suivre. Approche-le par le dessus ou par les flancs élevés.",
    ("hazard", "sombra"):      "Hazard reste mobile pour que Sombra ne puisse pas le hack facilement. Utilise ta mobilité verticale pour changer de niveau — Sombra suit mal les angles aériens.",

    # ── Emre (DPS mobile et résilient) ────────────────────────────────────────
    ("emre", "ashe"):          "Emre survit aux tirs d'Ashe grâce à ses capacités d'esquive. Joue en couverture, ressors pour riposter entre ses recharges — elle reload lentement.",
    ("emre", "soldier-76"):    "Emre contre Soldat:76 en zigzaguant pour éviter ses rafales. Sa précision diminue sur les cibles mobiles — reste en mouvement constant.",
    ("emre", "hanzo"):         "Emre esquive les flèches de Hanzo grâce à sa mobilité. Change de direction imprévisiblement — ses flèches chargées ratent les cibles rapides.",
    ("emre", "junkrat"):       "Emre survit aux combos de Junkrat en restant mobile. Ses grenades en arc sont inefficaces contre une cible qui change constamment d'altitude.",
    ("emre", "pharah"):        "Emre punit Pharah quand elle descend au sol. Maintiens une pression constante à mi-portée — elle doit atterrir pour recharger.",
    ("emre", "mercy"):         "Emre chasse Mercy grâce à sa survie et mobilité. Elle ne peut pas rester en vol indéfiniment — suis-la jusqu'à l'éliminer.",
    ("emre", "sombra"):        "Emre est difficile à one-shot même après un hack. Ses capacités passives restent actives — Sombra a du mal à l'éliminer seule sans suivi d'équipe.",
    ("emre", "echo"):          "Emre punit Echo au sol — elle ne peut pas copier une cible qu'elle ne peut pas atteindre. Reste actif sur elle pour l'empêcher d'atterrir sereinement.",

    # ── Sojourn vs Hanzo ──────────────────────────────────────────────────────
    ("sojourn", "hanzo"):      "Sojourn bat Hanzo au duel longue portée grâce à sa glissade. Utilise la glissade pour esquiver ses flèches chargées et réponds avec un tir chargé — il ne peut pas suivre une cible mobile.",

    # ── Winston vs flanqueurs ──────────────────────────────────────────────────
    ("winston", "sombra"):     "Winston plonge sur Sombra dès qu'elle sort de furtivité. Son tesla la suit même si elle retente le hack — garde-la sous pression constante.",

    # ── Kiriko vs compositions brawl ──────────────────────────────────────────
    ("kiriko", "junkrat"):     "Kiriko téléporte ses alliés hors des zones de combo de Junkrat. Utilise Suzu pour nettoyer les dégâts en cours — son pneu survie si toute l'équipe est soignée.",
    ("kiriko", "symmetra"):    "Kiriko téléporte ses alliés hors des rayons de Symmetra. Suzu nettoie les ralentissements — garde ta téléportation pour sortir les alliés pris dans ses tourelles.",
    ("kiriko", "torbjorn"):    "Kiriko maintient ses alliés en vie sous le feu de la tourelle de Torbjörn. Utilise Suzu pour annuler les dégâts de Surcharge — son ulti dure 6 secondes.",

    # ── Reinhardt vs Torbjörn ─────────────────────────────────────────────────
    ("reinhardt", "torbjorn"):  "Reinhardt avance avec le bouclier pour annuler la tourelle. Une fois au contact, Torbjörn ne peut rien faire — son marteau le détruit avant qu'il réagisse.",

    # ── Zenyatta vs compositions fermées ──────────────────────────────────────
    ("zenyatta", "symmetra"):  "Zenyatta pose l'Orbe de discorde sur Symmetra — chaque allié la détruit en quelques tirs. Ses tourelles fondent si tous les alliés ont l'Orbe d'harmonie.",
    ("zenyatta", "torbjorn"):  "Zenyatta place l'Orbe de discorde sur Torbjörn — sa tourelle détruit ses alliés mais lui fond rapidement. Cible Torbjörn lui-même, pas la tourelle.",
    ("zenyatta", "sojourn"):   "Zenyatta pose l'Orbe de discorde sur Sojourn — son tir chargé déjà puissant devient fatal pour elle aussi. Elle ne peut pas se permettre de prendre des coups.",

    # ── Baptiste vs compositions variées ──────────────────────────────────────
    ("baptiste", "hanzo"):     "Baptiste contre Hanzo car son Champ d'immortalité annule ses one-shots — place-le avant qu'il tire et force-le à gaspiller ses flèches chargées.",
    ("baptiste", "cassidy"):   "Baptiste bat Cassidy à mi-portée car son tir en rafale l'écrase en duel direct. Joue aggro sur lui — il n'a pas de mobilité pour fuir.",
    ("baptiste", "widowmaker"):"Baptiste contre Widowmaker car le Champ d'immortalité force ses tirs à ne pas conclure. Elle doit viser deux fois le même joueur — ça lui coûte du temps.",
    ("baptiste", "symmetra"):  "Baptiste bat Symmetra car sa lampe de soin tient l'équipe en vie sous ses rayons. Place le Champ d'immortalité dans les zones de tourelles pour avancer sereinement.",

    # ── Ana vs compositions variées ───────────────────────────────────────────
    ("ana", "mei"):            "Ana endort Mei au moment où elle tente de geler. La fléchette soporifique en plein souffle la coupe net — profites-en pour avancer et éliminer.",

    # ── Cassidy vs compositions variées ───────────────────────────────────────
    ("cassidy", "echo"):       "Cassidy contre Echo car la Grenade Magnétique colle même en plein vol. Attends qu'elle descende un peu puis flashbang + grenade pour l'éliminer.",
    ("cassidy", "reaper"):     "Cassidy contre Faucheur car le flashbang l'immobilise avant qu'il approche. Garde ton flash pour le moment où il téléporte — il arrive toujours au contact.",

    # ── Ashe vs compositions variées ──────────────────────────────────────────
    ("ashe", "mercy"):         "Ashe contre Mercy car B.O.B. la force à ne plus bouger pour soigner. Envoie B.O.B. sur la Mercy — elle doit fuir et ne peut plus faire de Guardian Angel.",
    ("ashe", "widowmaker"):    "Ashe bat Widowmaker au duel car sa cadence de tir est plus élevée. Joue en couverture, tire entre ses recharges — tu gagnes le duel d'attrition.",

    # ── Anran vs compositions variées ─────────────────────────────────────────
    ("anran", "widowmaker"):   "Anran punit Widowmaker depuis la mi-portée — sa cadence de tir la déborde avant qu'elle recharge. Reste derrière une couverture et tire entre ses rechargements.",

    # ── Genji vs flanqueurs ────────────────────────────────────────────────────
    ("genji", "sombra"):       "Genji contre Sombra car il peut deflect ses tirs quand elle sort de furtivité. Garde ton deflect pour le moment où elle hack — retourne ses dégâts sur elle.",
    ("genji", "tracer"):       "Genji contre Tracer car son dash peut l'attraper entre ses Blinks. Joue patient — frappe dans les courtes fenêtres entre ses téléportations.",
    ("genji", "reaper"):       "Genji contre Faucheur en le harcelant à mi-portée avec ses shurikens. Reste hors de sa portée effective (moins de 10m) — deflect ses tirs si il tente de s'approcher.",
}

# Fallback basé sur le subrole quand aucun matchup spécifique n'existe
SUBROLE_FALLBACK = {
    "initiator":  "prend les initiatives pour forcer des positions désavantageuses",
    "anchor":     "anchor solide qui tient le terrain",
    "brawler":    "domine au corps à corps",
    "disruptor":  "perturbe la composition ennemie",
    "flanker":    "flanque la backline et élimine les cibles isolées",
    "sniper":     "domine à longue portée",
    "area":       "contrôle les zones clés",
    "hybrid":     "s'adapte à plusieurs situations",
    "healer":     "maintient l'équipe en vie",
    "aggressive": "soigne tout en harcelant",
    "utility":    "apporte des utilitaires décisifs",
    "survivor":   "est très difficile à éliminer",
}

def build_reason(hero, covered_enemies, enemy_name_map, total_score):
    """Génère une explication pour chaque counter suggéré."""
    lines = []
    for enemy_slug in covered_enemies:
        key = (hero.slug, enemy_slug)
        if key in MATCHUP_REASONS:
            lines.append(MATCHUP_REASONS[key])
        else:
            enemy_name = enemy_name_map.get(enemy_slug, enemy_slug)
            fallback = SUBROLE_FALLBACK.get(hero.subrole, "est efficace dans cette composition")
            lines.append(f"{hero.name} {fallback} face à {enemy_name}.")

    if lines:
        return "\n".join(lines)
    return f"{hero.name} est un bon pick dans cette composition."

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
