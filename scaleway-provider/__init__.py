"""Scaleway Generative APIs as a Hermes model provider: ``--provider scaleway`` (alias ``scw``).

The API is OpenAI-compatible, so it can be reached without a plugin — a hand-written
``providers:`` custom block pointing at ``https://api.scaleway.ai/v1`` with
``SCW_SECRET_KEY`` — but that keeps the generic-endpoint defaults: an assumed 256K context
window instead of the model's real one (llama-3.3-70b-instruct has 100K,
mistral-small-3.2-24b-instruct-2506 128K, so compression runs too late), no per-model pricing
or reasoning/tool-call badges, no curated model list (the picker is the raw catalog, including
models that cannot drive an agent over chat-completions, such as gpt-oss-120b, whose
tool-calling Scaleway serves on the beta Responses API only), and no cheap auxiliary tier for
compression and summaries.

This profile keys models.dev's full ``scaleway`` row through ``models_dev_id``, so context
windows, pricing and capability badges resolve with no in-tree declarations.
``SCW_SECRET_KEY`` is the same secret key the Scaleway CLI and SDKs use; it is ambient
(``ambient_credentials``), so the provider is never auto-detected and turns on only when
explicitly selected. ``SCALEWAY_BASE_URL`` optionally overrides the default endpoint.
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
