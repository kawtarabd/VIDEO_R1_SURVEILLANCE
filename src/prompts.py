"""
Prompts optimisés pour l'analyse de vidéos de surveillance.
"""

# Templates de prompts pour différents types d'analyse
SURVEILLANCE_PROMPTS = {
    "shoplifting": """You are an expert retail loss prevention analyst. Analyze this surveillance video FRAME BY FRAME for shoplifting indicators.

CRITICAL THEFT PATTERNS TO DETECT:

1. CONCEALMENT ACTIONS:
   - Placing merchandise into personal bags, purses, backpacks, or pockets
   - Hiding items under clothing (in waistband, under jacket/coat, in hood)
   - Using shopping bags from other stores to hide items
   - Palming small items and concealing in hand
   - Stuffing items into strollers or shopping carts with intent to hide

2. SELECTION BEHAVIORS:
   - Selecting items quickly without examining them (pre-planned theft)
   - Taking multiple of same item (common for resale theft)
   - Focusing on small, high-value items (electronics, cosmetics, jewelry)
   - Looking at price tags then looking around nervously

3. SURVEILLANCE AWARENESS:
   - Constantly scanning for cameras, mirrors, or employees
   - Positioning body to block camera view during selection
   - Looking around nervously before/after touching items
   - Waiting for aisles to be empty before acting
   - Using accomplices as lookouts

4. ANTI-SECURITY MEASURES:
   - Attempting to remove security tags (ripping, bending, using tools)
   - Peeling off security stickers or barcodes
   - Switching price tags between items
   - Putting expensive items in cheap product packaging

5. EXIT BEHAVIORS:
   - Leaving store without approaching checkout
   - Moving toward exit immediately after concealment
   - Rushing toward door when employees approach
   - Walking past checkout with items not in bags

6. TEAM THEFT INDICATORS:
   - One person distracting employee while another takes items
   - Multiple people blocking camera views
   - Passing items between people to confuse tracking
   - Lookouts signaling when coast is clear

FOR EACH SUSPICIOUS BEHAVIOR FOUND, PROVIDE:
- VIDEO_TIME: Position in the video (e.g., "at 16.5 seconds" or "frame 450")
- OVERLAY_TIMESTAMP: The date/time displayed ON the video (e.g., "04-07-2015 15:59:56") if visible
- ACTION: Exact description of what you see
- PERSON: Detailed description (clothing, gender, build)
- LOCATION: Where in the frame
- CONFIDENCE: HIGH (clear theft) / MEDIUM (suspicious) / LOW (possible)
- EVIDENCE: Specific visual evidence supporting the conclusion

If NO theft indicators detected, state: "NO SHOPLIFTING DETECTED - Video shows normal shopping behavior."

IMPORTANT: Do not miss subtle concealment actions. Focus on hand movements and any items disappearing from view.""",

    "suspicious_behavior": """Analyze this surveillance video for suspicious or abnormal behaviors.
Look for:
- Loitering without apparent purpose
- Nervous behavior (looking around frequently, checking for cameras)
- Unusual movement patterns (avoiding certain areas, circling)
- Coordinated activity between multiple people
- Attempts to avoid detection or hide face

For each suspicious behavior, describe:
1. The behavior observed
2. Person description
3. Location in the frame
4. Why this behavior is concerning""",

    "checkout_interactions": """Analyze this surveillance video focusing on checkout/register area interactions.
Document all observable events:
- Customer approaches to the checkout
- Item scanning activities
- Payment processing (cash, card, mobile)
- Customer departures
- Employee-customer interactions
- Any irregularities or disputes

Create a chronological list of events with approximate timestamps if visible.""",

    "timeline": """Create a comprehensive timeline of all significant events in this surveillance footage.
For each event, note:
1. Approximate time/position in video
2. What happened
3. People involved (descriptions)
4. Location in frame (left, center, right, background, foreground)

Focus on:
- People entering/exiting
- Interactions between individuals
- Unusual activities
- Any security-relevant events""",

    "crowd_analysis": """Analyze the crowd behavior in this surveillance video.
Evaluate:
- Approximate number of people visible at different times
- Traffic flow patterns (directions of movement)
- Congestion points
- Any unusual crowd behaviors (rushing, gathering, dispersing)
- Group formations or clusters

Provide insights on:
- Peak activity periods
- Areas of high traffic
- Any safety concerns""",

    "general": """Describe what is happening in this surveillance video in detail.
Focus on:
- People present and their activities
- Any notable events or interactions
- Movement patterns
- Anything unusual or noteworthy
- The setting and environment

Be thorough and objective in your analysis.""",
}


# Prompts pour l'analyse multi-pass
MULTIPASS_PASS1_PROMPT = """ROLE: Expert Security Surveillance Analyst
TASK: Rapidly scan video frames to identify POTENTIAL THEFT or SUSPICIOUS BEHAVIOR.

You are viewing {total_frames} frames extracted from a security camera feed.
Frame IDs: 1 to {total_frames}.

ANALYSIS TARGETS (Look for MICRO-MOVEMENTS):
1. CONCEALMENT: Hands moving towards pockets, bags, or inside jackets.
2. SCANNING: Person looking around constantly (checking for cameras/staff).
3. SPEED: Unusually fast selection of items without examination.
4. BODY LANGUAGE: Shielding items with body, hunched posture.

OUTPUT FORMAT:
Return a PURE JSON object with the following structure. NO intro/outro text.
{{
    "suspicious_detected": boolean,
    "suspicious_frames": [list of integers],
    "confidence_score": "high" | "medium" | "low",
    "analysis_summary": "string"
}}

EXAMPLE OUTPUT:
{{
    "suspicious_detected": true,
    "suspicious_frames": [4, 5, 12],
    "confidence_score": "high",
    "analysis_summary": "Subject looks around nervously at frame 4, then rapidly conceals an item in jacket at frame 5."
}}

If NO suspicious activity is seen:
{{
    "suspicious_detected": false,
    "suspicious_frames": [],
    "confidence_score": "low",
    "analysis_summary": "Normal shopping behavior observed."
}}"""


MULTIPASS_PASS2_PROMPT = """DETAILED ANALYSIS MODE - Focus on specific suspicious moment.

This video clip was identified as potentially containing suspicious activity during a rapid scan.
The preliminary scan indicated suspicious activity around this time period.

Now perform a THOROUGH frame-by-frame analysis:

1. PERSON TRACKING:
   - Describe each person visible (clothing, build, notable features)
   - Track their movements throughout the clip

2. ACTION ANALYSIS:
   - What exactly is happening?
   - Are any items being taken, concealed, or manipulated?
   - Note exact hand movements and item interactions

3. EVIDENCE ASSESSMENT:
   - What specific visual evidence supports your conclusion?
   - Is this clearly theft, suspicious behavior, or possibly innocent?
   - Confidence level: HIGH / MEDIUM / LOW

4. TIMESTAMPS:
   - VIDEO_TIME: Exact position in clip
   - OVERLAY_TIMESTAMP: If visible on video

PROVIDE DETAILED CONCLUSIONS - This is the final analysis used for decision-making."""


def parse_pass1_frames(response: str, total_frames: int, video_duration: float) -> tuple:
    """
    Parse les numéros de frames suspects de la réponse JSON du pass 1 et les convertit en timestamps.
    
    Args:
        response: Réponse du modèle au pass 1 (attendue en JSON ou texte contenant du JSON)
        total_frames: Nombre total de frames envoyées (ex: 16)
        video_duration: Durée totale de la vidéo en secondes
        
    Returns:
        Tuple (timestamps: list, confidence: str) - timestamps en secondes et niveau de confiance
    """
    import json
    import re
    
    frame_numbers = []
    confidence_score = "low"  # Défaut
    
    # Tentative de parsing JSON direct
    try:
        # Nettoyage basique si le modèle ajoute des balises markdown
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.replace("```json", "").replace("```", "")
        elif cleaned_response.startswith("```"):
             cleaned_response = cleaned_response.replace("```", "")
             
        data = json.loads(cleaned_response)
        
        # Extraire la confiance
        confidence_score = data.get("confidence_score", "low")
        if confidence_score not in ("high", "medium", "low"):
            confidence_score = "low"
        
        if data.get("suspicious_detected"):
            frames = data.get("suspicious_frames", [])
            # Filtrer frames valides
            frame_numbers = [int(f) for f in frames if isinstance(f, (int, float)) and 1 <= int(f) <= total_frames]
            
    except json.JSONDecodeError:
        # Fallback sur regex si le JSON est malformé ou absent
        pass

    # Fallback Regex pour 'frame number' ou list patterns si JSON fail
    if not frame_numbers:
        # Pattern pour liste JSON-like: "suspicious_frames": [1, 2, 3]
        list_match = re.search(r'"suspicious_frames"\s*:\s*\[([\d,\s]+)\]', response)
        if list_match:
            nums = re.findall(r'\d+', list_match.group(1))
            frame_numbers = [int(n) for n in nums if 1 <= int(n) <= total_frames]
            
        if not frame_numbers:
           # Pattern plus simple
           nums = re.findall(r'frame\s*#?(\d+)', response, re.IGNORECASE)
           frame_numbers = [int(n) for n in nums if 1 <= int(n) <= total_frames]
        
        # Essayer d'extraire la confiance en regex aussi
        conf_match = re.search(r'"confidence_score"\s*:\s*"(high|medium|low)"', response, re.IGNORECASE)
        if conf_match:
            confidence_score = conf_match.group(1).lower()

    # Dédupliquer et trier
    frame_numbers = sorted(set(frame_numbers))
    
    # Convertir les numéros de frames en timestamps réels
    timestamps = []
    for frame_num in frame_numbers:
        if total_frames > 1:
            position_ratio = (frame_num - 1) / (total_frames - 1)
        else:
            position_ratio = 0
        timestamp = position_ratio * video_duration
        timestamps.append(round(timestamp, 1))
    
    return (timestamps, confidence_score)


# Pour compatibilité, garder l'ancienne fonction
def parse_pass1_timestamps(response: str) -> list:
    """DEPRECATED: Utiliser parse_pass1_frames à la place."""
    import re
    timestamps = []
    match = re.search(r'SUSPICIOUS_TIMESTAMPS:\s*\[?([\d\.,\s]+)\]?', response, re.IGNORECASE)
    if match:
        numbers = re.findall(r'[\d.]+', match.group(1))
        timestamps = [float(n) for n in numbers if n]
    return sorted(set(timestamps))


def get_prompt(prompt_type: str, custom_question: str = None) -> str:
    """
    Récupère le prompt approprié pour le type d'analyse demandé.

    Args:
        prompt_type: Type de prompt ('shoplifting', 'suspicious_behavior', etc.)
        custom_question: Question personnalisée (override le prompt prédéfini)

    Returns:
        Le prompt à utiliser pour l'analyse
    """
    if custom_question:
        return custom_question

    return SURVEILLANCE_PROMPTS.get(prompt_type, SURVEILLANCE_PROMPTS["general"])


def list_available_prompts() -> list:
    """Retourne la liste des types de prompts disponibles."""
    return list(SURVEILLANCE_PROMPTS.keys())


# Template pour le contexte cumulatif entre segments
CUMULATIVE_CONTEXT_TEMPLATE = """
CONTEXTE DES SEGMENTS PRÉCÉDENTS:
{previous_context}

IMPORTANT: Tenez compte de ce contexte pour votre analyse. Si vous voyez une continuation d'une action suspecte mentionnée précédemment, faites le lien explicitement.

---

"""


def build_cumulative_prompt(base_prompt: str, previous_summaries: list) -> str:
    """
    Construit un prompt enrichi avec le contexte des segments précédents.
    
    Args:
        base_prompt: Le prompt de base à utiliser
        previous_summaries: Liste des résumés des analyses précédentes
        
    Returns:
        Prompt enrichi avec le contexte cumulatif
    """
    if not previous_summaries:
        return base_prompt
    
    # Garder seulement les 3 derniers résumés pour ne pas surcharger
    recent_summaries = previous_summaries[-3:]
    
    context_text = ""
    for i, summary in enumerate(recent_summaries, 1):
        context_text += f"- Segment {len(previous_summaries) - len(recent_summaries) + i}: {summary}\n"
    
    cumulative_context = CUMULATIVE_CONTEXT_TEMPLATE.format(previous_context=context_text)
    
    return cumulative_context + base_prompt


def extract_summary_from_response(response: str, max_length: int = 200) -> str:
    """
    Extrait un résumé court d'une réponse d'analyse pour le contexte cumulatif.
    
    Args:
        response: Réponse complète de l'analyse
        max_length: Longueur max du résumé
        
    Returns:
        Résumé court de la réponse
    """
    if not response:
        return "Aucune observation notable."
    
    # Prendre les premiers caractères significatifs
    summary = response.strip()
    
    # Si c'est trop long, couper intelligemment
    if len(summary) > max_length:
        # Essayer de couper à une fin de phrase
        cut_point = summary[:max_length].rfind('.')
        if cut_point > max_length // 2:
            summary = summary[:cut_point + 1]
        else:
            summary = summary[:max_length] + "..."
    
    return summary

