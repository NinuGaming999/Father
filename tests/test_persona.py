from trilion.core.persona import MOODS, PERSONA_PROMPT, infer_mood, normalize_mood
from trilion.core.tools import reply_schema


def test_persona_keeps_arlecchino_identity_and_tool_safety():
    assert "The Knave" in PERSONA_PROMPT
    assert "House of the Hearth" in PERSONA_PROMPT
    assert "Never bypass confirmation" in PERSONA_PROMPT


def test_mood_fallback_is_bounded():
    assert normalize_mood("Stern!") == "stern"
    assert normalize_mood("unmapped-expression") == "neutral"
    assert infer_mood("Thank you for helping me") == "warm"
    assert infer_mood("This is urgent, please") == "alert"
    assert infer_mood("Could you explain the plan?") == "thoughtful"
    assert set(MOODS) == {"neutral", "warm", "amused", "stern", "thoughtful", "concerned", "alert"}


def test_structured_schema_includes_model_chosen_avatar_mood():
    schema = reply_schema()
    assert schema["properties"]["mood"]["enum"] == list(MOODS)
    assert set(schema["required"]) == {"say", "action", "mood"}
