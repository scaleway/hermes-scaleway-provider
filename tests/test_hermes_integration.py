"""End-to-end checks against a real Hermes checkout (skipped when Hermes is not importable).

Each check runs in a fresh interpreter whose HERMES_HOME holds an installed copy of the plugin
(``$HERMES_HOME/plugins/scaleway-provider``) and a ``.env`` with the credential, so Hermes
discovers and configures it the way it does after ``hermes plugins install scaleway-provider``.
Nothing talks to Scaleway: chat turns and the model-catalog probe go to Hermes' own scripted
loopback LLM (``tests/fakes/fake_llm_provider.py``) through ``SCALEWAY_BASE_URL``, which also
proves the override env var works on both paths.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

hermes_cli = pytest.importorskip("hermes_cli")

from conftest import PLUGIN_DIR, PROFILE  # noqa: E402  (after importorskip: no Hermes, no module import)

HERMES_ROOT = Path(hermes_cli.__file__).resolve().parents[1]
TOKEN = "scw-e2e-not-a-real-secret-key"
DEFAULT = PROFILE.fallback_models[0]


def _home(tmp_path: Path, base_url: str | None = None) -> Path:
    home = tmp_path / "hermes-home"
    shutil.copytree(PLUGIN_DIR, home / "plugins" / "scaleway-provider",
                    ignore=shutil.ignore_patterns("__pycache__"))
    env_text = f"SCW_SECRET_KEY={TOKEN}\n"
    if base_url:
        env_text += f"SCALEWAY_BASE_URL={base_url}\n"
    (home / ".env").write_text(env_text, encoding="utf-8", newline="\n")
    return home


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("OPENAI", "ANTHROPIC", "SCW", "SCALEWAY", "OPENROUTER", "HERMES_"))}
    env.update(HERMES_HOME=str(home), PYTHONPATH=str(HERMES_ROOT), NO_COLOR="1")
    return env


def _python(home: Path, code: str):
    """Run *code* in a fresh interpreter and return the JSON it prints last.

    The bootstrap mirrors what the real CLI does at startup (``hermes_cli.main`` calls
    ``load_hermes_dotenv``): ``$HERMES_HOME/.env`` values land in ``os.environ``, so the
    ``SCALEWAY_BASE_URL`` override reaches the paths that read it with ``os.getenv``."""
    bootstrap = "from hermes_cli.env_loader import load_hermes_dotenv; load_hermes_dotenv()\n"
    proc = subprocess.run([sys.executable, "-c", bootstrap + code], env=_env(home), cwd=str(home.parent),
                          capture_output=True, text=True, timeout=120, check=False)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_hermes_discovers_and_configures_the_installed_plugin(tmp_path):
    found = _python(_home(tmp_path), """
import json
from providers import get_provider_profile
from hermes_cli.auth import PROVIDER_REGISTRY
from hermes_cli.models import list_available_providers
from agent.models_dev import models_dev_id_for, models_dev_provider_map
profile = get_provider_profile("scaleway")
row = PROVIDER_REGISTRY.get("scaleway")
print(json.dumps({
    "alias": get_provider_profile("scw") is profile,
    "row_env": list(row.api_key_env_vars),
    "row_url_env": row.base_url_env_var,
    "picker": [p for p in list_available_providers() if p["id"] == "scaleway"],
    "models_dev": [models_dev_id_for("scaleway"), models_dev_provider_map()["scaleway"]],
}))
""")
    assert found["alias"] is True
    assert found["row_env"] == ["SCW_SECRET_KEY"]
    assert found["row_url_env"] == "SCALEWAY_BASE_URL"
    assert found["picker"] == [{"id": "scaleway", "label": "Scaleway", "aliases": [], "authenticated": True}]
    assert found["models_dev"] == ["scaleway", "scaleway"]


def test_the_catalog_probe_goes_to_the_override_url_with_the_key(tmp_path):
    """The live-catalog GET (and an explicit model switch) must follow SCALEWAY_BASE_URL and
    carry SCW_SECRET_KEY as the Bearer token — never the real endpoint."""
    fake = _fake_llm_module()
    with fake.FakeLLMServer([], api_key=TOKEN, record_get=True) as llm:
        found = _python(_home(tmp_path, llm.base_url), """
import json
from hermes_cli.models import provider_model_ids
from hermes_cli.model_switch import switch_model
switch = switch_model("fake-model", current_provider="openrouter", current_model="x",
                      explicit_provider="scaleway")
print(json.dumps({"ids": provider_model_ids("scaleway", force_refresh=True),
                  "switch": [switch.success, switch.target_provider, switch.base_url]}))
""")
        gets = [r for r in llm.requests if r["kind"] == "get"]
    assert gets, "no catalog GET reached the override endpoint"
    assert all(r["auth"] == f"Bearer {TOKEN}" for r in gets)
    # Curated-first merge: the fallback list leads, the live override catalog joins at the end.
    assert found["ids"] == [*PROFILE.fallback_models, "fake-model"]
    assert found["switch"] == [True, "scaleway", llm.base_url]


def test_a_real_turn_reaches_scaleway_endpoint_and_model(tmp_path):
    fake = _fake_llm_module()
    with fake.FakeLLMServer([fake.Text("pong")], api_key=TOKEN) as llm:
        home = _home(tmp_path, llm.base_url)
        (home / "config.yaml").write_text(
            f'model:\n  provider: scaleway\n  default: "{DEFAULT}"\n'
            "agent:\n  api_max_retries: 1\n",
            encoding="utf-8", newline="\n")
        proc = subprocess.run(
            [sys.executable, "-m", "hermes_cli.main", "chat", "-q", "Reply with: pong",
             "--oneshot", "-Q", "-t", "todo"],
            env=_env(home), cwd=str(home.parent), capture_output=True, text=True,
            timeout=240, check=False)
        assert proc.returncode == 0, (proc.stdout[-1000:], proc.stderr[-2000:])
        assert "pong" in proc.stdout
        requests = [(r["kind"], r["auth"], r["body"]) for r in llm.requests if r["kind"] in ("main", "aux")]
    assert requests, "the turn made no chat request"
    kinds = {r[0] for r in requests}
    assert "main" in kinds
    for kind, auth, body in requests:
        assert auth == f"Bearer {TOKEN}", f"{kind} request went out unauthenticated"
        assert body["model"] in (*PROFILE.fallback_models,), body["model"]
    main_bodies = [body for kind, _, body in requests if kind == "main"]
    assert main_bodies[0]["model"] == DEFAULT


def test_an_ambient_secret_key_is_never_autodetected(tmp_path):
    """The design rule: SCW_SECRET_KEY alone turns nothing on. Explicit selection is required.

    SCW_SECRET_KEY is the only credential in the home, so auto-detection would have to pick
    scaleway if the key were not ambient — on a clean home it refuses instead, and its error
    names no provider. On a machine with unrelated credentials, auto resolves to one of those —
    either way, never scaleway."""
    found = _python(_home(tmp_path), """
import json
from hermes_cli.runtime_provider import resolve_runtime_provider
try:
    auto = resolve_runtime_provider(requested=None)
    auto_out = [auto.get("provider"), auto.get("api_key"), ""]
except Exception as exc:
    auto_out = ["raised", type(exc).__name__, str(exc)]
explicit = resolve_runtime_provider(requested="scaleway")
print(json.dumps({"auto": auto_out,
                  "explicit": [explicit.get("provider"), explicit.get("api_key"),
                               explicit.get("base_url")]}))
""")
    assert found["auto"][0] != "scaleway"
    assert found["auto"][1] != TOKEN
    if found["auto"][0] == "raised":  # the only key in the home was skipped outright
        assert "scaleway" not in found["auto"][2]
    assert found["explicit"] == ["scaleway", TOKEN, "https://api.scaleway.ai/v1"]


def test_a_keyless_explicit_selection_names_the_env_var(tmp_path):
    home = _home(tmp_path)
    (home / ".env").write_text("", encoding="utf-8", newline="\n")
    found = _python(home, """
import json
from hermes_cli.runtime_provider import resolve_runtime_provider
try:
    resolve_runtime_provider(requested="scaleway")
    print(json.dumps({"error": None}))
except Exception as exc:
    print(json.dumps({"error": str(exc)}))
""")
    assert found["error"] is not None
    assert "SCW_SECRET_KEY" in found["error"]


def _fake_llm_module():
    path = HERMES_ROOT / "tests" / "fakes" / "fake_llm_provider.py"
    if not path.is_file():
        pytest.skip("this Hermes checkout has no tests/fakes/fake_llm_provider.py")
    spec = importlib.util.spec_from_file_location("hermes_fake_llm_provider", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
