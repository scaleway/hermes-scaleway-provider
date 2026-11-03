"""The profile without Hermes: registration, and the curated list against the recorded models.dev row."""

from __future__ import annotations

from conftest import MODELS_DEV, PROFILE, registered_profiles

ROW = MODELS_DEV["models"]
DEFAULT = "deepseek-v4.1-flash-1017"
AUX = "mistral-small-3.2-24b-instruct-2506"


def _vision_chat_models() -> dict[str, float]:
    """The recorded row's tool-calling models that accept images, priced per million input tokens."""
    priced = {}
    for model_id, entry in ROW.items():
        if not entry.get("tool_call") or "image" not in (entry.get("modalities") or {}).get("input", []):
            continue
        cost = (entry.get("cost") or {}).get("input")
        if cost is not None:
            priced[model_id] = cost
    return priced


def test_profile_registration():
    assert len(registered_profiles) == 1
    assert PROFILE.name == "scaleway"
    assert PROFILE.aliases == ("scw",)
    assert PROFILE.display_name == "Scaleway"
    assert PROFILE.signup_url == "https://console.scaleway.com/iam/api-keys"
    assert PROFILE.base_url == "https://api.scaleway.ai/v1"
    assert PROFILE.base_url_env_var == "SCALEWAY_BASE_URL"
    assert PROFILE.env_vars == ("SCW_SECRET_KEY", "SCALEWAY_BASE_URL")
    assert PROFILE.auth_type == "api_key"
    assert PROFILE.ambient_credentials is True
    assert PROFILE.models_dev_id == "scaleway"
    assert PROFILE.supports_vision is True
    assert PROFILE.default_aux_model == AUX
    assert PROFILE.fallback_models[0] == DEFAULT
    assert "gpt-oss-120b" not in PROFILE.fallback_models


def test_every_curated_model_is_in_the_recorded_models_dev_row():
    """models.dev resolves the metadata (context windows, pricing, badges); a curated id missing
    from the row would fall back to generic defaults. Retire ids that disappear and re-record
    the fixture when models.dev changes."""
    for model_id in (*PROFILE.fallback_models, AUX):
        entry = ROW.get(model_id)
        assert entry is not None, f"{model_id} is not in the recorded models.dev scaleway row"
        assert entry.get("tool_call") is True, f"{model_id} lost tool calling in models.dev"
        context = (entry.get("limit") or {}).get("context")
        assert isinstance(context, int) and context >= 64_000, model_id


def test_the_aux_model_is_the_cheapest_vision_capable_chat_model():
    """The README claim, checked against the recorded row: session titles and compression run on
    the cheapest tool-calling model that accepts images."""
    priced = _vision_chat_models()
    assert priced, "no priced vision-capable chat models in the recorded row"
    assert min(priced, key=priced.get) == AUX


def test_the_default_model_really_reasons():
    """The setup default is picked to lead an agent; the recorded row says it reasons, sees
    images and tool-calls."""
    entry = ROW[DEFAULT]
    assert entry.get("reasoning") is True and entry.get("tool_call") is True
    assert "image" in (entry.get("modalities") or {}).get("input", [])
