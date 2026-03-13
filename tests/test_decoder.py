"""Tests for decoder module."""
import json
import pytest
from unittest.mock import MagicMock, patch


SAMPLE_RESPONSE = {
    "neutrality_score": 7,
    "likely_intent": "Scheduling a routine check-in.",
    "emotional_tone": "Neutral/Professional",
    "what_they_probably_mean": "They want to sync on project status.",
    "reassurance": "This is a normal workplace interaction.",
    "suggested_responses": ["Sure! When works best?", "Happy to chat."],
}


def test_build_prompt_contains_text():
    """The user message should include the text to decode."""
    from decoder import build_messages
    messages = build_messages("We need to talk")
    user_msg = messages[-1]["parts"][0]
    assert "We need to talk" in user_msg


def test_parse_valid_response():
    """Should parse a valid JSON response from Gemini."""
    from decoder import parse_response
    result = parse_response(json.dumps(SAMPLE_RESPONSE))
    assert result["neutrality_score"] == 7
    assert result["emotional_tone"] == "Neutral/Professional"
    assert len(result["suggested_responses"]) == 2


def test_parse_valid_response_with_code_fences():
    """Should parse a JSON response wrapped in markdown code fences."""
    from decoder import parse_response
    raw = "```json\n" + json.dumps(SAMPLE_RESPONSE) + "\n```"
    result = parse_response(raw)
    assert result is not None
    assert result["neutrality_score"] == 7


def test_parse_invalid_json():
    """Should return None for invalid JSON."""
    from decoder import parse_response
    result = parse_response("This is not JSON at all")
    assert result is None


def test_parse_missing_fields():
    """Should return None if required fields are missing."""
    from decoder import parse_response
    result = parse_response('{"neutrality_score": 5}')
    assert result is None


@patch("decoder.genai")
def test_decode_text_calls_api(mock_genai):
    """Should call Gemini API and return parsed result."""
    from decoder import decode_text

    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(
        text=json.dumps(SAMPLE_RESPONSE)
    )

    result = decode_text("We need to talk", api_key="test-key")
    assert result["neutrality_score"] == 7
    mock_client.models.generate_content.assert_called_once()


@patch("decoder.genai")
def test_decode_text_nd_mode_uses_nd_prompt(mock_genai):
    """ND mode should use the neurodivergent system prompt."""
    from decoder import decode_text, SYSTEM_PROMPT_ND

    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(
        text=json.dumps(SAMPLE_RESPONSE)
    )

    decode_text("Hello", api_key="test-key", mode="nd")
    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs[1]["config"]["system_instruction"] == SYSTEM_PROMPT_ND


@patch("decoder.genai")
def test_decode_text_nt_mode_uses_nt_prompt(mock_genai):
    """NT mode should use the neurotypical system prompt."""
    from decoder import decode_text, SYSTEM_PROMPT_NT

    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(
        text=json.dumps(SAMPLE_RESPONSE)
    )

    decode_text("Hello", api_key="test-key", mode="nt")
    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs[1]["config"]["system_instruction"] == SYSTEM_PROMPT_NT


@patch("decoder.genai")
def test_clarify_text_mode_selection(mock_genai):
    """Clarify should use the correct prompt based on mode."""
    from decoder import clarify_text, CLARIFY_PROMPT_NT

    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.return_value = MagicMock(
        text="Clarification here."
    )

    clarify_text("some phrase", api_key="test-key", mode="nt")
    call_kwargs = mock_client.models.generate_content.call_args
    assert call_kwargs[1]["config"]["system_instruction"] == CLARIFY_PROMPT_NT


@patch("decoder.genai")
def test_decode_text_api_error(mock_genai):
    """Should return error dict on API failure."""
    from decoder import decode_text

    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("Network error")

    result = decode_text("We need to talk", api_key="test-key")
    assert "error" in result
