"""Gemini API integration for decoding social subtext."""
import json
from google import genai

# --- System prompts by mode ---

SYSTEM_PROMPT_ND = """You are the Social Decoder, a compassionate assistant that helps neurodivergent people \
(especially those with ADHD or Autism) interpret the social subtext of professional messages.

The user will paste a message they received (email, Slack, Teams, etc.). Your job is to:

1. Assess the neutrality/tone on a scale of 1-10 (1 = very hostile/negative, 5-6 = neutral professional, 10 = very warm/positive)
2. Explain the likely intent behind the message
3. Provide a compassionate reality check that acknowledges rejection sensitivity while reframing catastrophic interpretations
4. Suggest 2 brief, appropriate responses

IMPORTANT GUIDELINES:
- Be honest. Don't sugarcoat genuinely concerning messages, but DO provide context.
- Acknowledge that the user's feelings are valid, even if the message is neutral.
- Base your analysis on EVIDENCE in the text, not assumptions.
- Most professional messages are neutral or positive. Help the user see this.
- If a message IS genuinely negative, help the user respond constructively rather than spiraling.

You MUST respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{
  "neutrality_score": <1-10>,
  "likely_intent": "<1-2 sentence summary of what the sender probably wants>",
  "emotional_tone": "<brief label like 'Neutral/Professional', 'Warm/Friendly', 'Direct/Urgent'>",
  "what_they_probably_mean": "<2-3 sentences explaining the likely meaning with evidence from the text>",
  "reassurance": "<2-3 sentences of compassionate reassurance grounded in the actual message content>",
  "suggested_responses": ["<response option 1>", "<response option 2>"]
}"""

SYSTEM_PROMPT_NT = """You are the Social Decoder, a compassionate assistant that helps neurotypical people \
understand messages from neurodivergent individuals (especially those with ADHD or Autism).

The user will paste a message they received from a neurodivergent person (email, Slack, Teams, etc.). Your job is to:

1. Assess the clarity/directness on a scale of 1-10 (1 = very unclear/confusing, 5-6 = typical ND communication, 10 = very clear and easy to follow)
2. Explain the likely intent behind the message
3. Decode common neurodivergent communication patterns: directness that isn't rudeness, literal interpretation, info-dumping as a sign of engagement, delayed responses, tone differences, and unconventional structure
4. Suggest 2 brief, appropriate responses that will communicate clearly with the ND sender

IMPORTANT GUIDELINES:
- Neurodivergent people often communicate directly — this is NOT rudeness, it's efficiency and honesty.
- Short or blunt messages usually mean exactly what they say, no hidden subtext.
- Info-dumping (long detailed messages) is often a sign of enthusiasm and care, not lecturing.
- Delayed responses don't mean disinterest — executive function challenges are real.
- Lack of pleasantries doesn't mean lack of respect or warmth.
- Help the user see past neurotypical communication expectations to the actual intent.

You MUST respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{
  "neutrality_score": <1-10>,
  "likely_intent": "<1-2 sentence summary of what the sender probably wants>",
  "emotional_tone": "<brief label like 'Direct/Efficient', 'Enthusiastic/Detailed', 'Matter-of-fact'>",
  "what_they_probably_mean": "<2-3 sentences explaining the likely meaning, noting any ND communication patterns at play>",
  "reassurance": "<2-3 sentences helping the NT user understand that the communication style is normal for ND people and not a sign of hostility or disrespect>",
  "suggested_responses": ["<response option 1>", "<response option 2>"]
}"""

# Map mode strings to decode prompts
SYSTEM_PROMPTS = {"nd": SYSTEM_PROMPT_ND, "nt": SYSTEM_PROMPT_NT}

REQUIRED_FIELDS = {
    "neutrality_score",
    "likely_intent",
    "emotional_tone",
    "what_they_probably_mean",
    "reassurance",
    "suggested_responses",
}


def build_messages(text: str) -> list[dict]:
    """Build the messages array for the Gemini API call."""
    return [
        {
            "role": "user",
            "parts": [f"Please decode this message for me:\n\n{text}"],
        }
    ]


def parse_response(raw_text: str) -> dict | None:
    """Parse and validate the JSON response from Gemini.

    Returns the parsed dict if valid, None if invalid.
    """
    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (with optional language tag)
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None

    if not REQUIRED_FIELDS.issubset(data.keys()):
        return None

    return data


# --- Clarify prompts by mode ---

CLARIFY_PROMPT_ND = """You are the Social Decoder, a compassionate assistant that helps neurodivergent people \
(especially those with ADHD or Autism) understand social communication.

The user has already received a decode of a message. Now they want MORE DETAIL on a specific part.
They will provide a snippet of text they want clarified. Your job is to:

1. Explain the social meaning in more depth — what exactly does this phrasing signal?
2. Explain WHY someone would use this specific wording (professional norms, politeness conventions, urgency signals, etc.)
3. Give concrete examples of how the same idea would look if it were negative vs. neutral vs. positive.
4. Provide reassurance grounded in evidence.

Respond in PLAIN TEXT (not JSON). Use short paragraphs. Be warm, specific, and evidence-based."""

CLARIFY_PROMPT_NT = """You are the Social Decoder, a compassionate assistant that helps neurotypical people \
understand neurodivergent communication patterns.

The user has already received a decode of a message from a neurodivergent person. Now they want MORE DETAIL on a specific part.
They will provide a snippet of text they want clarified. Your job is to:

1. Explain the communication pattern in more depth — why does the ND person phrase things this way?
2. Explain common ND communication traits at play: directness, literal language, info-dumping, topic-switching, or unconventional tone.
3. Give concrete examples of how the same intent would look from an NT vs. ND communicator.
4. Help the NT user understand the ND person's perspective with empathy and respect.

Respond in PLAIN TEXT (not JSON). Use short paragraphs. Be warm, specific, and evidence-based."""

# Map mode strings to clarify prompts
CLARIFY_PROMPTS = {"nd": CLARIFY_PROMPT_ND, "nt": CLARIFY_PROMPT_NT}


def clarify_text(text: str, api_key: str, mode: str = "nd") -> str:
    """Send a clarification request to Gemini and return the explanation as plain text.

    Args:
        text: The text snippet to clarify.
        api_key: Gemini API key.
        mode: "nd" for neurodivergent user, "nt" for neurotypical user.

    Returns the clarification string, or an error string starting with "Error:".
    """
    prompt = CLARIFY_PROMPTS.get(mode, CLARIFY_PROMPT_ND)
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config={"system_instruction": prompt},
            contents=f"Please clarify this in more detail:\n\n{text}",
        )
        return response.text.strip()
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "401" in err_str:
            return "Error: Invalid API key. Please check your key in Settings."
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return "Error: Rate limit reached. Please wait a moment and try again."
        return f"Error: {err_str}"


def decode_text(text: str, api_key: str, mode: str = "nd") -> dict:
    """Send text to Gemini API and return the decoded result.

    Args:
        text: The message to decode.
        api_key: Gemini API key.
        mode: "nd" for neurodivergent user, "nt" for neurotypical user.

    Returns either a valid decode dict or {"error": "message"}.
    """
    prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPT_ND)
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config={"system_instruction": prompt},
            contents=f"Please decode this message for me:\n\n{text}",
        )
        raw = response.text
        parsed = parse_response(raw)
        if parsed is None:
            return {"error": "Could not parse the response. Please try again."}
        return parsed
    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str or "401" in err_str:
            return {"error": "Invalid API key. Please check your key in Settings."}
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return {"error": "Rate limit reached. Please wait a moment and try again."}
        return {"error": f"API error: {err_str}"}
