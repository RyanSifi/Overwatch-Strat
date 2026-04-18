"""
Views pour les héros, maps et counter-picker.
Tous les endpoints publics (aucune authentification requise).
"""
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Hero, Map, MetaComp, PatchNote
from .serializers import HeroSerializer, HeroListSerializer, MapSerializer, MetaCompSerializer, PatchNoteSerializer


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


# ─── Patch Notes ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def latest_patch(request):
    """GET /api/patches/latest/ — retourne uniquement le patch actuel (is_latest=True)."""
    try:
        patch = PatchNote.objects.get(is_latest=True)
    except PatchNote.DoesNotExist:
        patch = PatchNote.objects.first()
    if not patch:
        return Response({"error": "Aucun patch disponible."}, status=status.HTTP_404_NOT_FOUND)
    return Response(PatchNoteSerializer(patch).data)


# ─── Méta ────────────────────────────────────────────────────────────────────

class MetaCompListView(generics.ListAPIView):
    """GET /api/meta/  — liste toutes les comps méta. Filtre: ?style=dive|brawl|poke|rush|hybrid&tier=S"""
    permission_classes = [AllowAny]
    serializer_class   = MetaCompSerializer
    pagination_class   = None

    def get_queryset(self):
        qs    = MetaComp.objects.all()
        style = self.request.query_params.get("style")
        tier  = self.request.query_params.get("tier")
        if style: qs = qs.filter(style=style)
        if tier:  qs = qs.filter(tier=tier)
        return qs


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
                        "role":     h.role,
                        "tier":     h.tier,
                        "subrole":  h.subrole,
                        "is_new":   h.is_new,
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


# ─── Synergies ───────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def hero_synergies(request, slug):
    """
    GET /api/heroes/<slug>/synergies/
    Retourne les synergies d'un héros : alliés avec qui il est fort,
    triés par score décroissant, avec une explication textuelle.
    """
    try:
        hero = Hero.objects.get(slug=slug)
    except Hero.DoesNotExist:
        return Response({"error": f"Héros '{slug}' introuvable."}, status=status.HTTP_404_NOT_FOUND)

    result = []
    for ally_slug, score in sorted(hero.synergies.items(), key=lambda x: -x[1]):
        try:
            ally = Hero.objects.get(slug=ally_slug)
            reason_key = (slug, ally_slug)
            result.append({
                "slug":     ally.slug,
                "name":     ally.name,
                "role":     ally.role,
                "subrole":  ally.subrole,
                "tier":     ally.tier,
                "icon_url": ally.icon_url,
                "score":    score,
                "reason":   SYNERGY_REASONS.get(reason_key, ""),
            })
        except Hero.DoesNotExist:
            continue

    return Response({
        "hero":       HeroSerializer(hero).data,
        "synergies":  result,
    })


# Explications de synergies : (hero_slug, ally_slug) → raison
SYNERGY_REASONS = {
    # ── Ana ───────────────────────────────────────────────────────────────────
    ("ana", "genji"):       "Nano Blade : le Kiai boosté détruit plusieurs ennemis instantanément — la synergie la plus connue du jeu.",
    ("ana", "reinhardt"):   "Nano Earthshatter : Reinhardt chargé au Biostimulant + Smash de terrain = teamwipe quasi garanti.",
    ("ana", "reaper"):      "Nano Death Blossom : Faucheur devient invincible en tournant — élimine 4-5 héros si positionné au cœur du groupe.",
    ("ana", "soldier-76"):  "Nano Visor : le tracking de Soldat augmenté par le Biostimulant garantit les éliminations multiples.",
    ("ana", "winston"):     "Nano Primal Rage : Winston chargé saute partout et tue à coups de poing — impossible à gérer pour la backline.",
    ("ana", "roadhog"):     "Sleep Dart après le Hook : l'ennemi accroché + endormi avant le tir = mort assurée, sans échappatoire.",
    ("ana", "junker-queen"):"Grenade biotique + Rampage : JQ soignée massivement + Rampage applique Anti-Heal en zone = duo mortel.",
    ("ana", "dva"):         "Nano D.Va en mode boost : sa manoeuvrabilité + dégâts augmentés rend chaque Missile Micro dévastateur.",

    # ── Genji ─────────────────────────────────────────────────────────────────
    ("genji", "ana"):       "Nano Blade : voir Ana — la synergie la plus iconique d'Overwatch, teamwipe garanti si bien exécuté.",
    ("genji", "zenyatta"):  "Orbe de Discorde + 2 swings de Katana = élimination en moins de 2 secondes sur n'importe quel DPS.",
    ("genji", "kiriko"):    "Suzu annule les CC pendant le Blade, Swift Step permet à Kiriko d'être toujours aux côtés de Genji.",
    ("genji", "lucio"):     "Speed boost + dash Genji = flanqueur irrattrapable, impossible à anticiper ou à contrer.",
    ("genji", "mercy"):     "Mercy pocket pendant le Blade : les dégâts boostés sur plusieurs cibles garantissent le teamwipe.",

    # ── Lucio ─────────────────────────────────────────────────────────────────
    ("lucio", "reinhardt"):  "Rush combo : Speed Boost + Earthshatter = engagement ultra rapide inévitable sur toute la frontline.",
    ("lucio", "winston"):    "Dive accélérée : Winston saute + Lucio speed = les deux arrivent simultanément sur la backline.",
    ("lucio", "dva"):        "Double dive mobile : D.Va + Lucio s'engagent en simultané depuis deux angles différents.",
    ("lucio", "junker-queen"):"Rush brawl : JQ court déjà vite, le Speed Boost la rend impossible à fuir.",
    ("lucio", "genji"):      "Flanc irrattrapable : Genji + speed boost = aucun support ne peut l'esquiver.",
    ("lucio", "tracer"):     "Tracer encore plus mobile avec le Speed Boost — son Clin d'œil devient une arme de repositionnement absurde.",
    ("lucio", "mauga"):      "Speed Mauga : un Mauga en charge accélérée est impossible à fuir ou à CC efficacement.",
    ("lucio", "wrecking-ball"):"Ball + Speed = le Balling de Wrecking Ball génère encore plus de chaos.",

    # ── Mercy ─────────────────────────────────────────────────────────────────
    ("mercy", "pharah"):    "Pharmercy : vol permanent + Amplification de dégâts = combo incontestable si pas de hitscan.",
    ("mercy", "echo"):      "Rayon focalisé boosté : les dégâts d'Echo en phase de charge avec le boost sont dévastateurs.",
    ("mercy", "bastion"):   "Bastion Config Artillerie boosté : DPS maximal sur la cible depuis une position fixe sécurisée.",
    ("mercy", "soldier-76"):"Damage boost + Biostimulant = Soldat devient un DPS hypercarry en pocket.",
    ("mercy", "reinhardt"): "Résurrection de Reinhardt : ramener le tank en plein fight retourne complètement la situation.",

    # ── Reinhardt ─────────────────────────────────────────────────────────────
    ("reinhardt", "lucio"):  "Rush : Speed Boost + Earthshatter = la combinaison de brawl la plus efficace du jeu.",
    ("reinhardt", "zarya"):  "Graviton + Earthshatter : les ennemis aspirés par la Grav sont stun au sol = teamwipe total.",
    ("reinhardt", "ana"):    "Nano Earthshatter : Rein chargé + stun sol = aucune équipe ne survit à ça bien exécuté.",
    ("reinhardt", "brigitte"):"Brawl infranchissable : Brig soigne au hit derrière le bouclier, le duo push est imparable.",
    ("reinhardt", "zenyatta"):"Discord Orb + Rein swing : la cible discordée meurt en 2 swings de marteau.",
    ("reinhardt", "moira"):  "Moira soigne Rein en push constant — le bouclier + soin continu = front impénétrable.",
    ("reinhardt", "junkrat"):"Bouclier cache Junkrat qui spam ses grenades derrière — défense et pression combo parfaite.",

    # ── Zarya ─────────────────────────────────────────────────────────────────
    ("zarya", "hanzo"):     "Combo Grav Dragon : Graviton + Dragon Strike = teamwipe en 2 secondes — classique du méta OW.",
    ("zarya", "pharah"):    "Graviton + Barrage : les ennemis dans la Grav ne peuvent pas éviter les roquettes de Pharah.",
    ("zarya", "cassidy"):   "Graviton + Cowboy Deadeye : cibles immobiles dans la Grav = Deadeye garantit les OS.",
    ("zarya", "reinhardt"): "Double CC : Graviton regroupe + Earthshatter stun = toute l'équipe ennemie au sol.",
    ("zarya", "reaper"):    "Graviton + Death Blossom : Faucheur au cœur d'un groupe immobile = teamwipe instantané.",
    ("zarya", "lucio"):     "Son Mur de son dans la Grav force les ennemis à prendre les dégâts sans fuir.",
    ("zarya", "mei"):       "Mur de glace + Graviton : Mei sépare l'équipe, Zarya aspire les fragments isolés.",

    # ── Winston ───────────────────────────────────────────────────────────────
    ("winston", "tracer"):  "Dive coordonnée : Winston crée le chaos en frontline, Tracer élimine les supports isolés.",
    ("winston", "lucio"):   "Dive accélérée : Speed boost permet à Winston d'arriver en 0,5 seconde sur la backline.",
    ("winston", "dva"):     "Double tank dive : deux tanks mobiles submergent simultanément toute la backline.",
    ("winston", "genji"):   "Triple dive : Winston + Genji = supports débordés de partout, impossible de tout gérer.",
    ("winston", "kiriko"):  "Kiriko Swift Step sur Winston en frontline = heal instantané sur la cible la plus exposée.",
    ("winston", "sombra"):  "Sombra Hack + Winston jump = cible isolée sans capacités face à un tank agressif.",

    # ── D.Va ──────────────────────────────────────────────────────────────────
    ("dva", "lucio"):       "Speed boost D.Va = engagement ultra rapide, sa mobilité + vitesse = impossible à contrer.",
    ("dva", "winston"):     "Double dive : deux tanks convergent sur la backline depuis des angles différents.",
    ("dva", "tracer"):      "Dive + distraction : D.Va passe en force, Tracer finit les cibles affaiblies.",
    ("dva", "ana"):         "Nano D.Va boostée : son explosion de missiles fait des dégâts massifs en zone.",

    # ── Zenyatta ──────────────────────────────────────────────────────────────
    ("zenyatta", "genji"):      "Orbe de Discorde + 2 swings : n'importe quel DPS meurt en moins de 2 secondes.",
    ("zenyatta", "widowmaker"): "Discord Orb = Widowmaker OS en un seul tir chargé même sur les tanks.",
    ("zenyatta", "tracer"):     "Discord + burst Tracer = DPS combiné qui ignore les gros HP.",
    ("zenyatta", "reaper"):     "Discord + Death Blossom : Faucheur fait encore plus de dégâts sur une cible discordée.",
    ("zenyatta", "sojourn"):    "Discord + Railgun chargé : OS garanti sur n'importe qui, même avec gros HP.",

    # ── Kiriko ────────────────────────────────────────────────────────────────
    ("kiriko", "genji"):    "Suzu annule les CC pendant le Blade — Genji continue même sous AoE, Kiriko suit en Swift Step.",
    ("kiriko", "tracer"):   "Suzu sauve Tracer des CC létaux (Sleep, Flash, Crochet) qui l'auraient OS.",
    ("kiriko", "winston"):  "Swift Step sur Winston en frontline = heal instantané au bon endroit au bon moment.",
    ("kiriko", "lucio"):    "Double mobilité : Kiriko + Lucio = les deux supports les plus réactifs du jeu ensemble.",
    ("kiriko", "reaper"):   "Suzu annule les ralentissements et CC qui bloqueraient Faucheur en flanc.",

    # ── Brigitte ──────────────────────────────────────────────────────────────
    ("brigitte", "reinhardt"):  "Inspire soigne Rein au hit — le duo de brawl le plus résistant, le shield + heal = duo imprenable.",
    ("brigitte", "zarya"):      "Brawl : Bouclier de Zarya + Armor Packs Brig = combo survie au corps à corps.",
    ("brigitte", "lucio"):      "LúcioRio : Speed boost + Armor Packs = la meilleure composition de brawl du jeu.",
    ("brigitte", "junker-queen"):"JQ Rampage + Inspire = JQ inarrêtable avec soins constants en brawl.",
    ("brigitte", "mauga"):      "Inspire soigne Mauga en continu dans la mêlée — il ne meurt tout simplement pas.",

    # ── Orisa ─────────────────────────────────────────────────────────────────
    ("orisa", "bastion"):   "Javelin Spin + Bastion Config Artillerie : zone de contrôle absolute, personne ne passe.",
    ("orisa", "reaper"):    "Attraction de lance + Death Blossom : ennemis aspirés au cœur de la zone = wipe.",
    ("orisa", "hanzo"):     "Javelin Spin immobilise = Hanzo prend le temps de viser sans pression.",
    ("orisa", "cassidy"):   "Javelin Throw + Grenade Flash = double CC = mort garantie sur toute cible.",
    ("orisa", "junkrat"):   "Bouclier Orisa protège Junkrat qui spam ses grenades derrière en sécurité.",

    # ── Sigma ─────────────────────────────────────────────────────────────────
    ("sigma", "sojourn"):   "Flux de gravité immobilise = tir chargé Sojourn garanti sur une cible fixe.",
    ("sigma", "ashe"):      "Flux + Bob : Bob charge sur des cibles stun = impossible de s'échapper.",
    ("sigma", "ana"):       "Double poke longue portée : Sigma en frontline range + Ana sleep = zone sous contrôle.",
    ("sigma", "zenyatta"):  "Double poke : Discord + Sigma Hypersphères = pression continue à distance.",
    ("sigma", "widowmaker"):"Flux immobilise les cibles = Widowmaker OS garanti.",

    # ── Roadhog ───────────────────────────────────────────────────────────────
    ("roadhog", "ana"):     "Sleep Dart post-Hook : l'ennemi accroché + endormi avant le tir = mort assurée.",
    ("roadhog", "cassidy"): "Hook + Grenade Flash + Fan du Marteau = combo 3-pièces pour OS n'importe quel DPS.",
    ("roadhog", "moira"):   "Moira suit Roadhog en flanc et le soigne — il ne meurt pas en solo flanc.",
    ("roadhog", "zenyatta"):"Discord + Hook = la cible discordée meurt en 1 Hook au lieu de 2.",

    # ── Junker Queen ──────────────────────────────────────────────────────────
    ("junker-queen", "lucio"):   "Rush brawl : Speed Boost + JQ Rampage = engagement trop rapide pour être contré.",
    ("junker-queen", "brigitte"):"Rampage + Inspire : JQ applique Anti-Heal, Brig soigne tout le monde = combo brawl suprême.",
    ("junker-queen", "ana"):     "Grenade biotique + blessures JQ = aucun ennemi ne peut se soigner pendant Rampage.",
    ("junker-queen", "moira"):   "Moira soin soutenu en combat = JQ reste en vie pendant ses engagements suicidaires.",

    # ── Ramattra ──────────────────────────────────────────────────────────────
    ("ramattra", "reaper"):  "Annihilation + Death Blossom : ennemis bloqués dans la zone = Faucheur wipe en sécurité.",
    ("ramattra", "moira"):   "Confluence Moira + Form Ramattra : deux zones AoE simultanées = teamwipe si mal positionné.",
    ("ramattra", "ana"):     "Nano Annihilation : Ramattra invincible pendant sa Form avec le Biostimulant = imparable.",
    ("ramattra", "zenyatta"):"Discord + Bras Ramattra : la cible discordée meurt en 3 coups au lieu de 5.",

    # ── Mauga ─────────────────────────────────────────────────────────────────
    ("mauga", "brigitte"):  "Inspire soigne Mauga en continu dans la mêlée — Mauga dans un brawl avec Brig ne meurt pas.",
    ("mauga", "lucio"):     "Speed Mauga : un Mauga acceleré est impossible à fuir, il arrive avant qu'on réagisse.",
    ("mauga", "ana"):       "Grenade biotique annule les soins ennemis pendant que Mauga cage = aucune issue.",
    ("mauga", "moira"):     "Moira pocket Mauga pendant ses engagements — sa survie en combat devient absurde.",

    # ── Wrecking Ball ─────────────────────────────────────────────────────────
    ("wrecking-ball", "tracer"):  "Double dive chaos : Ball désoriente, Tracer élimine dans la confusion.",
    ("wrecking-ball", "lucio"):   "Speed + Balling : encore plus rapide pour les engagements et sorties.",
    ("wrecking-ball", "genji"):   "Ball perturbe la frontline, Genji arrive dans le dos pour finir les cibles isolées.",
    ("wrecking-ball", "sombra"):  "Hack sur cibles pile-driveés = ennemis sans défense face au chaos du Ball.",

    # ── Tracer ────────────────────────────────────────────────────────────────
    ("tracer", "winston"):  "Dive : Winston crée le chaos en frontline, Tracer élimine les supports dans le dos.",
    ("tracer", "lucio"):    "Speed boost Tracer = vitesse de déplacement irréelle, Blink devient une arme de gap-close.",
    ("tracer", "zenyatta"): "Discord Orb = Tracer OS en 1 clip au lieu de 2 chargeurs.",
    ("tracer", "kiriko"):   "Suzu + Rappel = Tracer a deux vies dans le même fight.",
    ("tracer", "wrecking-ball"):"Ball distraction = Tracer arrive dans le dos sans être ciblée.",

    # ── Soldat:76 ─────────────────────────────────────────────────────────────
    ("soldier-76", "ana"):      "Nano Visor : tracking + damage boost = multi-kill garanti en quelques secondes.",
    ("soldier-76", "mercy"):    "Mercy pocket + Biostimulant = Soldat hypercarry pratiquement inarrêtable.",
    ("soldier-76", "baptiste"): "Champ d'immortalité + Visor = Soldat fait ses dégâts sans risque d'être OS.",
    ("soldier-76", "lucio"):    "Speed boost + Biostimulant = Soldat en flanc surprise très difficile à anticiper.",

    # ── Sojourn ───────────────────────────────────────────────────────────────
    ("sojourn", "zenyatta"):    "Discord Orb = tir chargé Sojourn OS n'importe qui, même avec gros HP.",
    ("sojourn", "sigma"):       "Flux immobilise = tir chargé garanti sur une cible fixe, sans esquive possible.",
    ("sojourn", "lucio"):       "Speed boost = repositionnement éclair pour trouver les angles de tir idéaux.",
    ("sojourn", "kiriko"):      "Kitsune Rush accélère le tir de Sojourn, cadence doublée = DPS record.",

    # ── Ashe ──────────────────────────────────────────────────────────────────
    ("ashe", "baptiste"):   "Champ d'immortalité protège Bob — Bob dure toute sa durée sans être éliminé.",
    ("ashe", "sigma"):      "Flux + Bob : Bob charge sur des cibles stun, impossible d'esquiver.",
    ("ashe", "zenyatta"):   "Discord + tir Ashe = élimination à distance garantie en 2 tirs au lieu de 3.",
    ("ashe", "widowmaker"): "Double sniper depuis deux angles différents = impossible de se couvrir des deux.",

    # ── Widowmaker ────────────────────────────────────────────────────────────
    ("widowmaker", "zenyatta"):  "Discord = OS à longue distance garanti sur n'importe qui, tanks inclus.",
    ("widowmaker", "ashe"):      "Double angle poke : 2 snipers = impossible de se cacher des deux en même temps.",
    ("widowmaker", "sombra"):    "Sombra Hack immobilise la cible = Widowmaker OS garanti pendant le hack.",
    ("widowmaker", "hanzo"):     "Double sniper = contrôle total de la map, aucun angle sûr pour l'équipe ennemie.",

    # ── Hanzo ─────────────────────────────────────────────────────────────────
    ("hanzo", "zarya"):     "Combo Grav Dragon : la synergie classique OW — Graviton + Dragon Strike = teamwipe en 2s.",
    ("hanzo", "lucio"):     "Mur de son dans la Grav : Lucio place son ulte dans le Graviton pour forcer les ennemis.",
    ("hanzo", "sigma"):     "Flux regroupe les ennemis = Dragon Strike touche le maximum de cibles.",
    ("hanzo", "widowmaker"):"Double sniper = deux angles longs, aucun terrain n'est sûr.",

    # ── Pharah ────────────────────────────────────────────────────────────────
    ("pharah", "mercy"):    "Pharmercy : combo iconique — vol permanent + boost de dégâts = incontestable sans hitscan.",
    ("pharah", "baptiste"): "Champ d'immortalité protège Pharah au sol + Matrice d'amplification double ses dégâts.",
    ("pharah", "zarya"):    "Graviton + Barrage : ennemis immobiles dans la Grav = roquettes touchent à coup sûr.",
    ("pharah", "ana"):      "Nano Barrage : Pharah boostée + invincible pendant le Barrage = teamwipe garanti.",

    # ── Junkrat ───────────────────────────────────────────────────────────────
    ("junkrat", "reinhardt"): "Bouclier cache Junkrat : il spam ses grenades derrière en sécurité totale.",
    ("junkrat", "orisa"):     "Fortify avance, Junkrat spamme = combo défense et pression.",
    ("junkrat", "mei"):       "Mur de glace canalise les ennemis dans les grenades en arc = dégâts maximaux.",

    # ── Bastion ───────────────────────────────────────────────────────────────
    ("bastion", "mercy"):   "Mercy pocket Config Artillerie = DPS maximal, combo imparable si bien protégé.",
    ("bastion", "orisa"):   "Javelin Spin protège Bastion + Fortify avance = zone infranchissable.",
    ("bastion", "reinhardt"):"Bouclier devant Bastion Config Artillerie = combo défensif classique.",
    ("bastion", "baptiste"):"Champ d'immortalité + Matrice d'amplification = Bastion fait des dégâts records.",

    # ── Faucheur ──────────────────────────────────────────────────────────────
    ("reaper", "zarya"):    "Graviton + Death Blossom : groupe immobile = Faucheur wipe toute l'équipe seul.",
    ("reaper", "ramattra"): "Annihilation zone + Death Blossom : deux zones AoE en même temps = aucune issue.",
    ("reaper", "orisa"):    "Attraction de lance attire les ennemis = Faucheur en zone maximale dès l'arrivée.",
    ("reaper", "moira"):    "Moira suit Faucheur en flanc et le soigne — il ne meurt jamais en solo flanc.",
    ("reaper", "ana"):      "Nano Death Blossom : voir Ana — combo S-tier qui retourne n'importe quel fight.",

    # ── Symmetra ──────────────────────────────────────────────────────────────
    ("symmetra", "bastion"):  "Téléporteur repositionne Bastion sur un angle surprise = la défense devient une embuscade.",
    ("symmetra", "torbjorn"): "Double tourelle : Symm + Torb = flancs complètement verrouillés.",
    ("symmetra", "mei"):      "Mur de glace + Barrière photonique = zone infranchissable pendant plusieurs secondes.",
    ("symmetra", "reinhardt"):"Bouclier protège Symmetra qui place ses tourelles en sécurité = défense combo.",

    # ── Sombra ────────────────────────────────────────────────────────────────
    ("sombra", "wrecking-ball"): "Ball pile-drive + Sombra Hack = ennemis sans capacités en plein chaos.",
    ("sombra", "reaper"):        "Hack élimine la fuite ennemie + Death Blossom = aucune issue pour la cible.",
    ("sombra", "tracer"):        "Double flanc simultané : Sombra hack la frontline, Tracer finit la backline.",
    ("sombra", "winston"):       "Hack + Winston jump = cible isolée sans capacités face au tank agressif.",

    # ── Moira ─────────────────────────────────────────────────────────────────
    ("moira", "reaper"):        "Fade coordination : deux flancs simultanés submergent la backline de partout.",
    ("moira", "reinhardt"):     "Moira soin constant derrière le bouclier = la composition brawl la plus résiliente.",
    ("moira", "ramattra"):      "Confluence + Form Ramattra = deux zones AoE superposées = teamwipe zonal.",
    ("moira", "junker-queen"):  "Soin soutenu = JQ reste en vie pendant ses engagements les plus risqués.",
    ("moira", "mauga"):         "Moira pocket Mauga en combat = il ne meurt tout simplement pas en brawl.",

    # ── Baptiste ──────────────────────────────────────────────────────────────
    ("baptiste", "soldier-76"): "Champ d'immortalité + Visor = Soldat fait ses dégâts sans risque d'être OS.",
    ("baptiste", "pharah"):     "Immortalité protège Pharah + Matrice double ses dégâts = combo aérien record.",
    ("baptiste", "reinhardt"):  "Matrice d'amplification sur les alliés de Rein = dégâts en push doublés.",
    ("baptiste", "ana"):        "Double healer burst : Ana grenade + Baptiste burst = survie d'équipe maximale.",
    ("baptiste", "ashe"):       "Matrice d'amplification double les dégâts d'Ashe = tireur d'élite en surpuissance.",

    # ── Cassidy ───────────────────────────────────────────────────────────────
    ("cassidy", "zarya"):   "Graviton + Cowboy Deadeye : cibles immobiles dans la Grav = Deadeye OS garantis.",
    ("cassidy", "orisa"):   "Javelin Throw + Grenade Flash = double CC = mort garantie sur toute cible.",
    ("cassidy", "ana"):     "Nano + Deadeye : dégâts boostés pendant la visée = éliminations ultra rapides.",
    ("cassidy", "sigma"):   "Flux immobilise = Deadeye OS garanti sur des cibles figées.",

    # ── Torbjörn ──────────────────────────────────────────────────────────────
    ("torbjorn", "reinhardt"):  "Bouclier cache la tourelle Torb = personne ne peut la détruire sans percer le shield.",
    ("torbjorn", "symmetra"):   "Double tourelle : flancs complètement verrouillés pour la défense.",
    ("torbjorn", "mercy"):      "Mercy pocket la tourelle niveau 2 = DPS de tourelle maximal.",
    ("torbjorn", "orisa"):      "Fortify bloque l'avance + tourelle Torb contrôle la zone = défense tanky.",

    # ── Mei ───────────────────────────────────────────────────────────────────
    ("mei", "zarya"):   "Mur de glace + Graviton : Mei sépare + Zarya aspire = teamwipe en deux temps.",
    ("mei", "hanzo"):   "Mur canalise les ennemis vers le Dragon Strike = touchés garantis.",
    ("mei", "junkrat"): "Mur bloque la fuite + grenades Junkrat sur les ennemis coincés = dégâts maximaux.",
    ("mei", "reinhardt"):"Mur sépare l'équipe ennemie + Earthshatter sur les fragments isolés.",

    # ── Echo ──────────────────────────────────────────────────────────────────
    ("echo", "mercy"):  "Mercy boost + Rayon focalisé : dégâts de burst records sur une cible en phase de charge.",
    ("echo", "ana"):    "Echo copie Ana = double Nano possible en un même fight.",
    ("echo", "zenyatta"):"Discord + Rayon focalisé = burst combiné qui détruit en moins d'une seconde.",
    ("echo", "zarya"):  "Echo copie Zarya = double Graviton en un combat = deux teamwipes possibles.",

    # ── Venture ───────────────────────────────────────────────────────────────
    ("venture", "lucio"):   "Speed boost permet à Venture d'arriver encore plus vite de sous terre.",
    ("venture", "ana"):     "Grenade biotique annule les soins ennemis pendant que Venture sort avec son AoE.",
    ("venture", "kiriko"):  "Suzu protège Venture des CC qui bloqueraient sa sortie de terrier.",

    # ── Nouveaux héros ────────────────────────────────────────────────────────
    ("hazard", "lucio"):        "Speed boost + mobilité verticale de Hazard = engagements depuis les hauteurs en un instant.",
    ("hazard", "ana"):          "Nano Hazard en plein engage vertical = impossible à contrer.",
    ("hazard", "brigitte"):     "Inspire soigne Hazard en brawl — son agressivité de tank est soutenue en continu.",
    ("hazard", "junker-queen"): "Double tank brawl agressif : Hazard + JQ submergent la frontline ennemie.",

    ("domina", "zenyatta"):     "Discord + pression Domina = cible débordée depuis deux fronts simultanément.",
    ("domina", "ana"):          "Nano Domina en engage = impossible de l'arrêter quand elle est chargée.",
    ("domina", "reaper"):       "Domina attire les ennemis + Death Blossom = teamwipe en zone.",
    ("domina", "moira"):        "Moira suit Domina et la soigne — le duo brawl le plus résistant.",

    ("anran", "reinhardt"):     "Bouclier Rein protège Anran qui poke à haute cadence derrière en sécurité.",
    ("anran", "junker-queen"):  "JQ engage en frontline pendant qu'Anran poke depuis la mi-portée = pression double.",
    ("anran", "mauga"):         "Mauga absorbe les dégâts en front, Anran poke derrière = duo poke-brawl.",
    ("anran", "orisa"):         "Orisa tient la zone, Anran spam sa cadence derrière la protection.",

    ("mizuki", "tracer"):       "Suivi mobile + Tracer = deux flanqueurs en synergie dans la backline.",
    ("mizuki", "genji"):        "Mizuki soutient Genji depuis le flanc, ensemble ils submergent les supports.",
    ("mizuki", "kiriko"):       "Double support mobile : combo de mobilité maximale, toujours au bon endroit.",
    ("mizuki", "wrecking-ball"):"Mizuki suit Ball dans son chaos pour soigner au plus près.",

    ("freja", "zenyatta"):      "Discord + Freja longue portée = cible exposée détruite rapidement.",
    ("freja", "sigma"):         "Flux immobilise = Freja prend le temps de viser sans risque.",
    ("freja", "ana"):           "Grenade biotique annule les soins pendant que Freja accumule les dégâts.",

    ("sierra", "zenyatta"):     "Discord + Sierra snipe = OS garanti sur n'importe quelle cible.",
    ("sierra", "orisa"):        "Orisa immobilise les ennemis = Sierra prend ses angles en sécurité totale.",
    ("sierra", "baptiste"):     "Matrice d'amplification double les dégâts de Sierra = sniper en surpuissance.",

    ("wuyang", "lucio"):        "Speed boost + mobilité Wuyang = engage agressif difficile à anticiper.",
    ("wuyang", "brigitte"):     "Inspire soigne Wuyang en brawl — son agressivité est soutenue en permanence.",
    ("wuyang", "ana"):          "Nano Wuyang en engage = force de frappe maximale.",

    ("jetpack-cat", "lucio"):   "Double mobilité : JetpackCat + Speed Boost = duo dive ultra rapide.",
    ("jetpack-cat", "winston"): "Double dive aérien : Winston + JetpackCat = backline débordée sous deux axes.",
    ("jetpack-cat", "tracer"):  "Triple dive : JetpackCat + Tracer + Winston = chaos total sur la backline.",

    ("vendetta", "sombra"):     "Sombra Hack immobilise = Vendetta burst depuis le flanc en toute sécurité.",
    ("vendetta", "tracer"):     "Double flanqueur : Vendetta + Tracer = deux assassins simultanés en backline.",
    ("vendetta", "wrecking-ball"):"Ball désoriente = Vendetta arrive dans le dos pendant la confusion.",

    ("emre", "reinhardt"):      "Bouclier protège Emre qui engage depuis un angle sûr.",
    ("emre", "zarya"):          "Graviton + burst Emre = cibles immobiles = dégâts maximaux.",
    ("emre", "orisa"):          "Orisa contrôle la zone = Emre prend ses engagements en sécurité.",
}


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
    ("reinhardt", "torbjorn"):  "Reinhardt avance bouclier levé pour annuler entièrement la tourelle — derrière le bouclier aucun allié ne prend de dégâts. Une fois au contact il détruit la tourelle d'un marteau et Torbjörn n'a aucune mobilité pour fuir.",
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
    # ── Hazard (tank mobile, piques de contrôle + escalade verticale) ───────────
    ("hazard", "venture"):     "Hazard place ses piques exactement à la sortie du terrier de Venture — dès qu'il émerge du sol, les piques lui infligent des dégâts immédiats. Anticipe sa direction et pose ta zone avant qu'il sorte.",
    ("hazard", "reaper"):      "Hazard pose un rideau de piques entre lui et Faucheur, puis prend de la hauteur — Faucheur doit traverser les piques pour approcher et ne peut pas le viser depuis le bas. Joue sur ta verticalité pour qu'il ne puisse jamais entrer dans sa fenêtre de dégâts.",
    ("hazard", "cassidy"):     "Hazard esquive le Flashbang de Cassidy en bougeant verticalement au moment du lancer — le Flashbang doit atterrir à tes pieds pour te toucher. Monte sur un rebord ou saute dès qu'il engage pour que la grenade atterrisse dans le vide.",
    ("hazard", "soldier-76"):  "Hazard prend les hauteurs hors de la trajectoire des rafales de Soldat:76 — ses tirs sont optimisés pour la mi-portée en ligne droite, pas en angle vertical. Depuis un rebord élevé, tes piques couvrent le sol et lui rendent l'approche impossible.",
    ("hazard", "ashe"):        "Hazard bondit sur Ashe depuis un angle élevé avant qu'elle ait le temps de charger son tir — elle a besoin de 0,7 seconde pour viser, et ton approche aérienne ne lui laisse pas cette fenêtre. Si elle tire B.O.B., tes piques le ralentissent.",
    ("hazard", "widowmaker"):  "Hazard change constamment de niveau vertical — Widowmaker doit recharger entre chaque tir chargé, et pendant ce temps tu changes de position. Elle ne peut pas te suivre avec un scope si tu passes du sol au plafond entre chaque échange.",
    ("hazard", "symmetra"):    "Hazard détruit les tourelles de Symmetra depuis les hauteurs avec ses piques — les tourelles ne peuvent pas ajuster leur angle de tir vers le haut pour le cibler. Plonge sur les tourelles une par une depuis les rebords élevés qu'elles ne couvrent pas.",
    ("hazard", "torbjorn"):    "Hazard descend sur la tourelle de Torbjörn depuis un angle vertical où elle ne peut pas pivoter suffisamment — la tourelle a un angle de rotation limité. Torbjörn lui-même n'a aucune mobilité pour esquiver les piques au sol.",
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
    # ── Emre (DPS résilient, survie exceptionnelle, flanc) ────────────────────
    ("emre", "tracer"):        "Emre encaisse les burst de Tracer sans mourir grâce à sa survie passive — quand elle vide ses chargeurs sur lui il est encore debout et riposte, obligeant Tracer à Recall sans élimination. Elle gaspille ses ressources sur une cible qui ne tombe pas.",
    ("emre", "genji"):         "Emre absorbe le combo de Genji avec sa survie et contre-attaque pendant le dash — le burst initial ne le tue pas, il riposte après l'engagement au moment où Genji est le plus exposé. Genji s'attend à one-combo sa cible, pas à se retrouver en duel prolongé.",
    ("emre", "zenyatta"):      "Emre dive sur Zenyatta et absorbe le Discord Orb avec sa survie native — même discordé il tient assez longtemps pour l'éliminer. Zenyatta n'a aucune mobilité pour fuir, et ses 200 HP fondent dès qu'Emre est au contact.",
    ("emre", "widowmaker"):    "Emre approche Widowmaker en zigzaguant entre les couvertures — elle a besoin d'une cible stable pour charger son tir. Sa survie lui permet d'absorber un tir non chargé sans être éliminé, puis il ferme la distance avant sa recharge.",

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
    # ── Mizuki (support tactique, soins constants haute cadence) ─────────────
    ("mizuki", "roadhog"):     "Mizuki soigne ses alliés assez vite pour compenser les one-shots de Roadhog — son crochet + Cochon entier tente de tuer en une seconde, mais si l'allié ciblé a ses soins actifs il survit. Garde tes soins en priorité sur la cible de son crochet.",
    ("mizuki", "mauga"):       "Mizuki tient la frontline en vie pendant que Mauga vide ses deux mitrailleuses — sa cadence de soins élevée surpasse le volume de feu soutenu de Mauga sur la durée. Mauga gagne les fights courts, Mizuki gagne les fights longs.",
    ("mizuki", "orisa"):       "Mizuki annule l'effet d'isolement d'Orisa — quand la Javeline projette un allié, Mizuki lui transfère ses soins immédiatement pour qu'il survive l'exposition. Son burst heal compense les fenêtres où les alliés sont hors de couverture.",
    ("mizuki", "reinhardt"):   "Mizuki soigne l'équipe pendant la charge de Reinhardt — son burst heal sauve les alliés projetés au mur avant qu'il enchaîne le marteau. Après la charge, elle resoigne pendant qu'il est exposé sans bouclier.",
    ("mizuki", "tracer"):      "Mizuki soigne ses alliés plus vite que Tracer ne peut les tuer sur une seule cible — Tracer a besoin de vider ses 150 balles pour éliminer, et Mizuki restaure les HP entre chaque clip. Tracer doit changer de cible en permanence, ce qui réduit son efficacité.",
    ("mizuki", "genji"):       "Mizuki maintient ses alliés en vie pendant le combo de Genji — ses soins rapides annulent son burst sur une cible, forçant Genji à se retirer sans élimination ou à rester engagé trop longtemps. Elle transforme chaque dive de Genji en risque pour lui.",
    ("mizuki", "wrecking-ball"):"Mizuki soigne l'équipe dispersée par Wrecking Ball — même quand Ball projette tout le monde dans des directions différentes, sa portée de soins couvre la zone pour stabiliser les HP. La disruption de Ball fonctionne moins bien si personne ne meurt de l'isolement.",
    ("mizuki", "ashe"):        "Mizuki contre Ashe en soignant les alliés pris dans ses lignes de mire — ses soins constants tiennent les alliés en vie entre les tirs chargés. B.O.B. fonctionne moins bien quand personne ne tombe bas assez longtemps pour être éliminé.",
    ("mizuki", "hanzo"):       "Mizuki annule les picks de Hanzo en soignant les alliés à HP partiels avant qu'il recharge — ses flèches chargées sont puissantes mais lentes à préparer. Mizuki réduit la fenêtre où ses alliés sont vulnérables entre les échanges.",
    # ── Wuyang (support défensif, boucliers et utilitaires de protection) ────
    ("wuyang", "genji"):       "Wuyang place son bouclier défensif sur l'allié ciblé par Genji juste avant que le combo arrive — le bouclier absorbe la première passe et donne le temps à l'allié de se repositionner. Genji s'attend à one-combo une cible nue, pas une cible bouclée.",
    ("wuyang", "tracer"):      "Wuyang réagit à la Bombe à impulsion de Tracer avec son utilitaire défensif — dès que Tracer colle la bombe il active la protection sur l'allié ciblé, ce qui réduit ou annule l'explosion. Tracer gaspille son ulti sans élimination.",
    ("wuyang", "sombra"):      "Wuyang maintient ses alliés hackés en vie avec ses boucliers passifs — même sans leurs capacités ils ont la protection de Wuyang pour survivre les 1,5 secondes du hack. Sombra perd son avantage si les alliés hackés ne meurent pas.",
    ("wuyang", "roadhog"):     "Wuyang bouclier l'allié dans la ligne de mire de Roadhog avant le crochet — si l'allié a un bouclier actif au moment du combo crochet/Cochon entier il survit. Garde ton utilitaire pour réagir dès que Roadhog lève son crochet.",
    ("wuyang", "widowmaker"):  "Wuyang distribue ses boucliers défensifs en rotation sur les alliés exposés — Widowmaker a besoin d'une cible non bouclée pour confirmer son pick. Elle doit attendre la fin du bouclier pour viser, ce qui lui fait perdre son timing.",
    ("wuyang", "ashe"):        "Wuyang protège ses alliés des tirs chargés d'Ashe avec ses boucliers — elle a besoin de 0,5 seconde pour charger, et pendant ce temps Wuyang peut activer sa protection. B.O.B. ne peut pas être bouclé mais les alliés vivants le gèrent ensemble.",
    ("wuyang", "hanzo"):       "Wuyang réagit aux flèches chargées de Hanzo en bouclant les alliés visibles — ses flèches one-shot les 200 HP mais pas une cible avec bouclier actif. Tourne tes boucliers sur les alliés les plus exposés à sa sightline.",
    ("wuyang", "freja"):       "Wuyang bloque le burst de Freja au moment où elle arrive sur la backline — son bouclier sur le soignant visé lui donne le temps de reculer. Freja perd son momentum si sa première attaque ne tue pas.",
    # ── Jetpack Cat (support aérien, soins depuis les hauteurs) ──────────────
    ("jetpack-cat", "genji"):  "Jetpack Cat soigne ses alliés depuis les airs, hors d'atteinte des shurikens de Genji — il maintient le niveau de HP des alliés pendant toute la séquence du combo. Genji doit one-combo sa cible sinon Jetpack Cat resoigne avant qu'il recharge.",
    ("jetpack-cat", "tracer"): "Jetpack Cat repositionne rapidement ses soins depuis les airs pour suivre Tracer qui change de cible — dès que Tracer vide ses balles sur un allié, Jetpack Cat est déjà au-dessus pour restaurer les HP. Tracer ne peut pas épuiser les soins aériens.",
    ("jetpack-cat", "sombra"): "Jetpack Cat est difficile à hack en altitude — Sombra doit monter à portée hack (15m) mais Jetpack Cat voit l'approche depuis les hauteurs. Même si hackée, elle reste en l'air et garde sa portée de soins.",
    ("jetpack-cat", "roadhog"): "Jetpack Cat est impossible à crocheter depuis les airs — Roadhog a besoin d'une cible au sol pour son crochet, et Jetpack Cat soigne ses alliés crochétés depuis une position hors d'atteinte. Il force Roadhog à passer à un autre style.",
    ("jetpack-cat", "ashe"):   "Jetpack Cat soigne ses alliés depuis un angle vertical qu'Ashe ne couvre pas — elle vise horizontalement et B.O.B. ne peut pas cibler les hauteurs. Depuis les airs, Jetpack Cat annule ses picks en maintenant les HP à niveau.",
    ("jetpack-cat", "hanzo"):  "Jetpack Cat reste en mouvement aérien perpétuel ce qui rend le tir chargé de Hanzo quasi impossible — il a besoin d'une fenêtre de 0,5 seconde sur une cible stable. Depuis les airs Jetpack Cat est une cible trop erratique pour ses flèches.",
    ("jetpack-cat", "bastion"): "Jetpack Cat soigne ses alliés depuis un angle que Bastion en mode Artillerie ne couvre pas facilement — Bastion est statique et vise horizontalement. Un soignant aérien rend son volume de feu moins décisif.",
    ("jetpack-cat", "cassidy"): "Jetpack Cat en altitude échappe au Flashbang de Cassidy — la grenade doit atterrir à ses pieds et il est trop haut. Ses alliés flashbangés restent soignés pendant la période d'étourdissement.",
    # ── Freja (DPS mobile à haute vélocité, burst rapide) ────────────────────
    ("freja", "zenyatta"):     "Freja arrive sur Zenyatta en moins d'une seconde grâce à sa vitesse de déplacement — il n'a pas d'outil de fuite et ses 200 HP fondent en deux échanges à courte portée. Approche par un angle oblique pour éviter son Discord Orb initial.",
    ("freja", "widowmaker"):   "Freja ferme la distance sur Widowmaker avant qu'elle charge son tir — elle a besoin de 0,7 seconde pour un tir chargé, et Freja parcourt cette distance en 0,5 seconde. Approche entre ses tirs, pas pendant la charge.",
    ("freja", "ana"):          "Freja arrive sur Ana trop vite pour qu'elle place sa Fléchette soporifique — le projectile met 0,3 seconde à l'atteindre et Freja est déjà au contact. Si Ana rate son sleep elle n'a plus d'outil pour survivre seule.",
    ("freja", "mercy"):        "Freja suit Mercy dans chaque Guardian Angel grâce à sa vitesse de déplacement — même quand Mercy saute d'allié en allié Freja ferme la distance. Attaque au moment où elle atterrit, avant qu'elle enclenche le prochain saut.",
    ("freja", "lucio"):        "Freja rattrape Lucio en mur-ride grâce à sa vitesse de base supérieure — même en Boost de vitesse il ne crée pas assez de distance. Coupe sa trajectoire sur le mur plutôt que de le poursuivre en ligne droite.",
    ("freja", "torbjorn"):     "Freja rush sur Torbjörn avant qu'il déploie sa tourelle — elle prend 3 secondes à s'installer et Freja arrive en 1 seconde. Sans tourelle active Torbjörn est un DPS fragile sans mobilité.",
    ("freja", "bastion"):      "Freja flanque Bastion depuis son angle mort — en mode Artillerie il ne peut pas pivoter rapidement et son arc de tir frontal ne couvre pas les côtés. Approche par le flanc droit ou gauche, jamais de face.",
    ("freja", "lifeweaver"):   "Freja élimine Lifeweaver avant qu'il utilise son Tiraillement végétal — la vitesse de Freja ne lui laisse pas le temps d'activer la capacité. Même s'il téléporte un allié, Freja s'en prend directement à lui.",
    # ── Sierra (DPS flanqueur précis, angles perpendiculaires) ───────────────
    ("sierra", "zenyatta"):    "Sierra cible Zenyatta depuis un flanc perpendiculaire à sa ligne de mire — il est occupé à viser la frontline et ne voit pas l'angle latéral. Depuis le flanc il ne peut pas placer son Discord Orb à temps et ses 200 HP ne résistent pas.",
    ("sierra", "widowmaker"):  "Sierra prend un angle perpendiculaire à la sightline de Widowmaker — elle vise dans une direction et Sierra approche depuis le côté. Widowmaker doit pivoter de 90° pour répondre, ce qui lui coûte 1 seconde qu'elle n'a pas.",
    ("sierra", "ana"):         "Sierra approche Ana depuis son angle aveugle — le flanc opposé à sa ligne de soins. Si Ana ne la voit pas arriver, sa Fléchette soporifique doit être tirée en réaction, pas en anticipation, ce qui réduit ses chances de toucher.",
    ("sierra", "bastion"):     "Sierra contourne Bastion à 90° depuis son flanc — en mode Artillerie son arc de rotation est limité. Approche par le côté et attaque sa tranche arrière où il ne peut pas répondre rapidement.",
    ("sierra", "torbjorn"):    "Sierra prend la tourelle de Torbjörn depuis un angle qu'elle ne couvre pas — les tourelles ont un angle de tir frontal limité. Entre dans sa zone morte par le flanc et détruis-la avant que Torbjörn pivote pour se défendre.",
    ("sierra", "lucio"):       "Sierra coupe la route de Lucio sur son mur en s'interposant sur son axe de déplacement — elle anticipe sa trajectoire et l'attend au lieu de le poursuivre. Un Lucio intercepté n'a plus de vitesse pour s'échapper.",
    ("sierra", "mercy"):       "Sierra anticipe les Guardian Angels de Mercy depuis le flanc — elle observe où Mercy va sauter et se positionne sur cet allié avant l'atterrissage. Mercy atterrit directement dans l'angle de Sierra.",
    ("sierra", "lifeweaver"):  "Sierra élimine Lifeweaver depuis le flanc avant qu'il réagisse — son Tiraillement végétal est une compétence à activer, pas un réflexe. Depuis l'angle latéral il ne la voit pas assez tôt pour l'utiliser.",
    # ── Vendetta (DPS assassin, burst instantané, flanc furtif) ──────────────
    ("vendetta", "zenyatta"):  "Vendetta arrive dans le dos de Zenyatta sans être détecté — il enchaîne son burst avant que Zenyatta place le Discord Orb. Ses 200 HP ne résistent pas à un burst de flanqueur depuis le dos, et il n'a aucune compétence de fuite.",
    ("vendetta", "widowmaker"):"Vendetta apparaît dans l'angle mort de Widowmaker — elle vise vers la frontline et ne couvre pas son dos. Approche depuis derrière sa position en longeant les bords de la map, elle n'a aucune compétence de mêlée pour se défendre.",
    ("vendetta", "ana"):       "Vendetta arrive trop vite pour qu'Ana place sa Fléchette soporifique avec précision — depuis le dos elle doit pivoter de 180° avant de tirer, ce qui lui laisse 0,3 seconde. Si elle rate le sleep elle n'a plus rien pour survivre seule.",
    ("vendetta", "reinhardt"): "Vendetta contourne le bouclier de Reinhardt par les côtés pour atteindre la backline — Reinhardt ne peut pas pivoter avec son bouclier pour couvrir tous les angles. Pendant qu'il fait face à la frontline Vendetta est déjà derrière.",
    ("vendetta", "bastion"):   "Vendetta attaque Bastion sous son angle mort latéral — en mode Artillerie il ne peut pas pivoter rapidement et son tourret ne couvre pas les flancs. Entre à 90° de sa ligne de tir et vide ton burst avant qu'il réagisse.",
    ("vendetta", "sigma"):     "Vendetta passe les boucliers de Sigma en approchant par les angles non couverts — son bouclier est unidirectionnel et Vendetta contourne par le flanc opposé. Sigma n'a pas d'outil de mêlée pour se défendre une fois contourné.",
    ("vendetta", "mercy"):     "Vendetta traque Mercy dans chaque Guardian Angel — sa mobilité de flanqueur lui permet de suivre ses déplacements entre alliés. Elle atterrit toujours quelque part, et Vendetta l'attend à destination.",
    ("vendetta", "lifeweaver"):"Vendetta élimine Lifeweaver avant qu'il puisse téléporter un allié — son burst est instantané et Lifeweaver doit activer manuellement son Tiraillement végétal. Un Lifeweaver surpris depuis le flanc n'a pas le temps d'activer quoi que ce soit.",

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
    ("hazard", "hanzo"):       "Hazard monte sur les hauteurs avant Hanzo et occupe ses angles de sightline — Hanzo ne peut pas viser vers le bas sous ses pieds si Hazard est sur le même rebord. Pose des piques dans la zone où Hanzo veut se positionner pour l'en chasser.",
    ("hazard", "junkrat"):     "Hazard plonge sur Junkrat depuis les airs là où ses grenades en arc ne peuvent pas monter — ses projectiles suivent une courbe vers le bas et ne peuvent pas atteindre une cible qui approche par le dessus. Approche en angle aérien steep, pas en ligne droite.",
    ("hazard", "sombra"):      "Hazard change constamment de niveau vertical pour sortir de la portée hack de Sombra — elle doit rester à moins de 15m pendant 0,65 seconde, et Hazard interrompt cette fenêtre en montant ou descendant. Reste toujours en mouvement vertical.",
    ("hazard", "anran"):       "Hazard dive sur Anran qui n'a aucune mobilité défensive pour fuir — il encaisse ses tirs en approchant et l'atteint avant qu'il vide son chargeur. Anran perd toute efficacité dès qu'une cible est sur lui.",

    # ── Emre (DPS mobile et résilient) ────────────────────────────────────────
    ("emre", "ashe"):          "Emre sort de couverture entre les tirs chargés d'Ashe — elle met 0,5 seconde à charger et recharge lentement après. Sa survie lui permet d'absorber un tir non chargé sans être éliminé, puis il ferme la distance pendant sa recharge.",
    ("emre", "soldier-76"):    "Emre zigzague latéralement pour sortir du cone de précision des rafales de Soldat:76 — sa précision chute sur les cibles qui se déplacent perpendiculairement. Un Emre qui bouge en oblique force Soldat:76 à pulser son Biostimulant défensivement.",
    ("emre", "hanzo"):         "Emre change de direction imprévisiblement toutes les 0,5 secondes — Hanzo doit anticiper la position de sa cible lors du tir, et une cible qui change d'axe constamment ne peut pas être anticipée. Sa survie absorbe une flèche non chargée.",
    ("emre", "junkrat"):       "Emre change constamment d'altitude et de direction, rendant les grenades en arc de Junkrat quasi impossibles à placer — elles doivent atterrir à ses pieds et Emre n'est jamais là où Junkrat vise. Sa survie absorbe les dégâts de zone partiels.",
    ("emre", "pharah"):        "Emre punit Pharah quand elle doit atterrir pour recharger — elle ne peut pas rester en l'air indéfiniment. Maintiens une pression constante à mi-portée pour l'empêcher de prendre des angles aériens sûrs.",
    ("emre", "mercy"):         "Emre suit Mercy dans ses Guardian Angels grâce à sa mobilité — elle doit toujours atterrir quelque part et Emre absorbe ses tirs défensifs avec sa survie. Suis-la de Guardian Angel en Guardian Angel, elle n'a pas assez de fuel pour fuir indéfiniment.",
    ("emre", "sombra"):        "Emre est impossible à one-shot après un hack — ses mécaniques de survie sont passives et restent actives même sans capacités. Sombra a besoin d'un suivi d'équipe immédiat pour l'éliminer, et ce suivi est souvent absent.",
    ("emre", "echo"):          "Emre punit Echo quand elle doit atterrir pour attaquer — elle ne peut pas combattre efficacement en vol continu. Reste sur elle au sol, sa survie lui permet de rester dans l'échange jusqu'à ce qu'elle soit éliminée.",

    # ── Sojourn vs Hanzo ──────────────────────────────────────────────────────
    ("sojourn", "hanzo"):      "Sojourn bat Hanzo au duel longue portée grâce à sa glissade. Utilise la glissade pour esquiver ses flèches chargées et réponds avec un tir chargé — il ne peut pas suivre une cible mobile.",

    # ── Winston vs flanqueurs ──────────────────────────────────────────────────
    ("winston", "sombra"):     "Winston plonge sur Sombra dès qu'elle sort de furtivité. Son tesla la suit même si elle retente le hack — garde-la sous pression constante.",

    # ── Kiriko vs compositions brawl ──────────────────────────────────────────
    ("kiriko", "junkrat"):     "Kiriko téléporte ses alliés hors des zones de combo de Junkrat. Utilise Suzu pour nettoyer les dégâts en cours — son pneu survie si toute l'équipe est soignée.",
    ("kiriko", "symmetra"):    "Kiriko téléporte ses alliés hors des rayons de Symmetra. Suzu nettoie les ralentissements — garde ta téléportation pour sortir les alliés pris dans ses tourelles.",
    ("kiriko", "torbjorn"):    "Kiriko maintient ses alliés en vie sous le feu de la tourelle de Torbjörn. Utilise Suzu pour annuler les dégâts de Surcharge — son ulti dure 6 secondes.",

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

    # ── Anran (DPS poke longue portée, haute cadence, cible les statiques) ───
    ("anran", "widowmaker"):   "Anran punit Widowmaker depuis la mi-portée — sa cadence de tir élevée la déborde avant qu'elle recharge son tir chargé. Reste en couverture et expose-toi seulement entre ses rechargements pour accumuler les dégâts.",
    ("anran", "zenyatta"):     "Anran harcèle Zenyatta depuis la mi-portée avec son taux de tir élevé — ses 200 HP ne résistent pas longtemps à un poke soutenu. Zenyatta doit se cacher pour soigner, ce qui coupe ses soins sur l'équipe.",
    ("anran", "ana"):          "Anran force Ana à se mettre à couvert avec son poke continu — elle ne peut pas soigner et esquiver en même temps. Chaque seconde qu'elle passe en couverture est une seconde sans soins pour son équipe.",
    ("anran", "mercy"):        "Anran traque Mercy avec son poke à haute cadence — elle ne peut pas rester statique pour soigner sans prendre des dégâts constants. Résurrection en plein poke d'Anran est très risquée, elle ne peut pas canal-caster sereinement.",
    ("anran", "orisa"):        "Anran accumule des dégâts sur Orisa malgré son armure — sa cadence de tir élevée contourne mieux l'armure que les gros projectiles espacés. Poke derrière une couverture et profite que son Bouclier de javeline est en cooldown.",
    ("anran", "sigma"):        "Anran vide le bouclier de Sigma plus vite qu'il ne se régénère grâce à sa cadence de tir — le bouclier a 1500 HP et une régénération différée. Poke en continu pour l'épuiser, puis expose ton équipe sur Sigma sans protection.",
    ("anran", "bastion"):      "Anran poke Bastion depuis la mi-portée pendant qu'il est statique en mode Artillerie — Bastion ne peut pas se repositionner et Anran accumule des dégâts depuis une couverture à mi-portée. Sa cadence de tir rivalise avec le volume de feu de Bastion à distance.",
    ("anran", "reinhardt"):    "Anran poke le bouclier de Reinhardt jusqu'à l'épuiser — le bouclier a 1600 HP et Anran a la cadence pour le vider. Une fois le bouclier cassé Reinhardt est exposé et son équipe n'a plus de protection frontale.",
    ("anran", "lifeweaver"):   "Anran traque Lifeweaver avec son poke en continu — il ne peut pas soigner et esquiver simultanément à mi-portée. Un Lifeweaver sous pression constante fait des Tiraillements végétaux précipités.",

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
