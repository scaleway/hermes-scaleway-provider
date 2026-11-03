"""Shared helpers: the plugin loaded against a stand-in ``providers`` package, and the recorded data.

The unit tests run without Hermes. ``load_plugin`` imports the plugin with small stand-ins for
``providers`` and ``providers.base`` and restores ``sys.modules`` afterwards, so a real Hermes
on the path (the end-to-end tests, or a developer checkout) is left untouched. A Hermes source
checkout is located for the end-to-end module (``HERMES_SOURCE`` or a sibling ``hermes-agent``
directory); without one, that module skips itself.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "scaleway-provider"
HERE = Path(__file__).resolve().parent
# models.dev's `scaleway` provider row (context windows, pricing, tool-call/vision/reasoning
# flags), recorded 2026-11-03 from https://models.dev/api.json.
MODELS_DEV = json.loads((HERE / "scaleway_models_dev.json").read_text(encoding="utf-8"))


class StubProfile:
    """Stands in for ``providers.base.ProviderProfile``."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


def load_plugin():
    """Import the plugin once against the stand-ins; returns (module, registered profiles)."""
    registered: list = []
    providers = types.ModuleType("providers")
    providers.register_provider = registered.append
    base = types.ModuleType("providers.base")
    base.ProviderProfile = StubProfile
    providers.base = base
    saved = {name: sys.modules.get(name) for name in ("providers", "providers.base")}
    sys.modules.update({"providers": providers, "providers.base": base})
    try:
        spec = importlib.util.spec_from_file_location(
            "scaleway_provider_under_test", PLUGIN_DIR / "__init__.py",
            submodule_search_locations=[str(PLUGIN_DIR)])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for name, previous in saved.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
    return module, registered


plugin, registered_profiles = load_plugin()
PROFILE = registered_profiles[0] if registered_profiles else None


def _prepend_hermes_source() -> None:
    """Make a Hermes checkout importable for the end-to-end module, when one is around.

    CI passes PYTHONPATH; locally ``HERMES_SOURCE`` or a sibling ``hermes-agent`` works. Only the
    path is prepared — nothing is imported here, so unit runs without Hermes stay fast.
    """
    import os

    source = os.environ.get("HERMES_SOURCE") or str(ROOT.parent / "hermes-agent")
    if (Path(source) / "hermes_cli" / "__init__.py").is_file() and source not in sys.path:
        sys.path.insert(0, source)


_prepend_hermes_source()
