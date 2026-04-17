"""
View proxy pour l'API Claude (Anthropic).
La clé API n'est JAMAIS exposée au frontend — tous les appels passent par ce proxy.
"""
import json

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Prompt système envoyé à Claude pour garantir un JSON structuré
SYSTEM_PROMPT = """Tu es un coach Overwatch expert niveau Diamant/Masters.
Tu analyses des compositions d'équipe et fournis des conseils concis et actionnables.

IMPORTANT : Ta réponse doit être UNIQUEMENT un objet JSON valide, sans texte avant ni après.
Format attendu :
{
  "strengths": ["point fort 1", "point fort 2", "point fort 3"],
  "weaknesses": ["faiblesse 1", "faiblesse 2", "faiblesse 3"],
  "suggestions": [
    { "action": "Action concrète", "reason": "Explication courte" },
    { "action": "Action concrète", "reason": "Explication courte" }
  ]
}

Règles :
- Maximum 3 points forts, 3 faiblesses, 3 suggestions
- Chaque entrée : 1-2 phrases max, directe et pratique
- Cite les noms des héros dans tes analyses
- Adapte au rang indiqué (Gold/Plat = conseils simples et applicables)
"""


@api_view(["POST"])
@permission_classes([AllowAny])
def analyze_composition(request):
    """
    POST /api/coach/analyze/
    Body :
    {
        "ally":  ["zarya", "genji", "tracer", "ana", "zenyatta"],
        "enemy": ["sigma", "sojourn", "ashe", "kiriko", "lucio"],
        "map":   "kings-row",
        "phase": "Point de capture",
        "rank":  "gold"
    }
    Retourne :
    {
        "strengths":   ["..."],
        "weaknesses":  ["..."],
        "suggestions": [{"action": "...", "reason": "..."}]
    }
    """
    # Validation des données entrantes
    ally   = request.data.get("ally", [])
    enemy  = request.data.get("enemy", [])
    map_name = request.data.get("map", "inconnue")
    phase  = request.data.get("phase", "")
    rank   = request.data.get("rank", "gold")

    if not ally or not enemy:
        return Response(
            {"error": "Les champs 'ally' et 'enemy' sont requis."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(ally) > 6 or len(enemy) > 6:
        return Response(
            {"error": "Maximum 6 héros par équipe."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Vérifie la disponibilité de la clé Anthropic
    if not ANTHROPIC_AVAILABLE:
        return Response(
            {"error": "Module Anthropic non installé."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-..."):
        return Response(
            {"error": "Clé API Anthropic non configurée dans .env"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Construction du prompt utilisateur
    phase_info = f", phase : {phase}" if phase else ""
    user_prompt = (
        f"Analyse cette composition Overwatch :\n\n"
        f"Map : {map_name}{phase_info}\n"
        f"Rang : {rank}\n\n"
        f"Équipe alliée  : {', '.join(ally)}\n"
        f"Équipe ennemie : {', '.join(enemy)}\n\n"
        f"Donne ton analyse en JSON."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = message.content[0].text.strip()

        # Parse le JSON retourné par Claude
        try:
            analysis = json.loads(raw_text)
        except json.JSONDecodeError:
            # Si Claude n'a pas respecté le format JSON, on extrait ce qu'on peut
            return Response(
                {
                    "strengths":   ["Analyse disponible en texte brut"],
                    "weaknesses":  [],
                    "suggestions": [{"action": raw_text[:200], "reason": "Format inattendu de Claude"}],
                    "raw": raw_text,
                }
            )

        # Valide la structure
        return Response({
            "strengths":   analysis.get("strengths",   [])[:3],
            "weaknesses":  analysis.get("weaknesses",  [])[:3],
            "suggestions": analysis.get("suggestions", [])[:3],
        })

    except anthropic.AuthenticationError:
        return Response(
            {"error": "Clé API Anthropic invalide."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except anthropic.RateLimitError:
        return Response(
            {"error": "Limite de requêtes Anthropic atteinte. Réessaie dans quelques secondes."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    except anthropic.APIError as e:
        return Response(
            {"error": f"Erreur API Anthropic : {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        return Response(
            {"error": f"Erreur inattendue : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
