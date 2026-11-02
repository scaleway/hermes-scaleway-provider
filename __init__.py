"""Scaleway Generative APIs provider profile.

Standalone Hermes model-provider plugin, discovered from
``$HERMES_HOME/plugins/scaleway-provider/`` after a
``hermes plugins install scaleway-provider`` (or a direct copy).
"""

from providers import register_provider
from providers.base import ProviderProfile

scaleway = ProviderProfile(
    name="scaleway", aliases=("scw",), display_name="Scaleway",
    description="Scaleway Generative APIs — European OpenAI-compatible inference (pay-per-use)",
    signup_url="https://console.scaleway.com/iam/api-keys", env_vars=("SCW_SECRET_KEY", "SCALEWAY_BASE_URL"),
    base_url="https://api.scaleway.ai/v1", base_url_env_var="SCALEWAY_BASE_URL",
    auth_type="api_key",
    # SCW_SECRET_KEY is ambient (the Scaleway CLI and SDKs export it too), so it
    # is never auto-detected as the inference provider: explicit config only.
    ambient_credentials=True,
    # models.dev carries a full `scaleway` row (context windows, pricing,
    # reasoning/tool-call badges); the profile keys it, no in-tree map entry.
    models_dev_id="scaleway",
    # Chat Completions accepts image content in messages, tool results included.
    supports_vision=True,
    default_aux_model="mistral-small-3.2-24b-instruct-2506",
    # [0] is the setup default. Serverless models that tool-call on the
    # chat-completions wire; gpt-oss-120b is deliberately absent — Scaleway
    # serves its tool-calling on /v1/responses only (Responses API, beta).
    fallback_models=(
        "deepseek-v4.1-flash-1017",
        "glm-5.3", "glm-5.2",
        "qwen3.5-397b-a17b", "qwen3.8-27b", "qwen3.6-35b-a3b",
        "mistral-medium-3.5-128b", "mistral-small-3.2-24b-instruct-2506",
        "gemma-4-26b-a4b-it", "llama-3.3-70b-instruct", "qwen3-235b-a22b-instruct-2507",
    ),
)

register_provider(scaleway)
