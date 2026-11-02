"""Standalone-discovery contract for the scaleway provider profile.

Every assertion holds with the plugin installed ONLY as a user plugin
(``$HERMES_HOME/plugins/scaleway-provider/``) against a Hermes tree that has no
bundled scaleway: what the catalog ships is what users get.
"""
import pytest


def _profile():
    from providers import get_provider_profile

    return get_provider_profile("scaleway")


def test_user_plugin_layer_discovers_profile():
    from providers import list_providers

    names = [p.name for p in list_providers()]
    assert "scaleway" in names


def test_alias_resolves_to_same_profile():
    from providers import get_provider_profile

    assert get_provider_profile("scw") is _profile()


def test_endpoint_and_credential_wiring():
    profile = _profile()
    assert profile.base_url == "https://api.scaleway.ai/v1"
    assert profile.base_url_env_var == "SCALEWAY_BASE_URL"
    assert profile.env_vars == ("SCW_SECRET_KEY", "SCALEWAY_BASE_URL")
    assert profile.auth_type == "api_key"
    # The secret key is ambient (Scaleway CLI/SDKs export it too): never auto-detected.
    assert profile.ambient_credentials is True


def test_models_dev_metadata_wiring():
    """Capability metadata (context windows, badges) resolves through models.dev
    with no in-tree PROVIDER_TO_MODELS_DEV entry: the profile keys it."""
    from agent.models_dev import models_dev_id_for, models_dev_provider_map

    assert models_dev_id_for("scaleway") == "scaleway"
    assert models_dev_provider_map()["scaleway"] == "scaleway"


def test_model_curatorship():
    profile = _profile()
    assert profile.fallback_models[0] == "deepseek-v4.1-flash-1017"
    assert profile.default_aux_model == "mistral-small-3.2-24b-instruct-2506"
    assert "gpt-oss-120b" not in profile.fallback_models
    assert profile.supports_vision is True


def test_auth_resolves_scw_secret_key(monkeypatch):
    from hermes_cli.runtime_provider import resolve_runtime_provider

    monkeypatch.setenv("SCW_SECRET_KEY", "scw-test-secret")
    resolved = resolve_runtime_provider(requested="scaleway")
    assert "api.scaleway.ai" in str(resolved.get("base_url", ""))


def test_keyless_run_names_the_env_var(monkeypatch):
    from hermes_cli.runtime_provider import resolve_runtime_provider

    monkeypatch.delenv("SCW_SECRET_KEY", raising=False)
    with pytest.raises(Exception, match="SCW_SECRET_KEY"):
        resolve_runtime_provider(requested="scaleway")
