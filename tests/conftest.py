"""Test harness: install this plugin into a throwaway Hermes home.

Runs before any test module imports hermes, so ``providers`` discovery (lazy, first
``list_providers()``) scans the temp home with the plugin in it. ``HERMES_SOURCE`` points
at a Hermes checkout to test against (default: a sibling ``hermes-agent`` directory);
test against a clean ``main`` so the bundled tree cannot satisfy the assertions.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HERMES_SOURCE = Path(os.environ.get("HERMES_SOURCE", REPO_ROOT.parent / "hermes-agent")).resolve()
if not (HERMES_SOURCE / "providers" / "base.py").is_file():
    raise SystemExit(f"no Hermes source at {HERMES_SOURCE}; set HERMES_SOURCE to a checkout")
sys.path.insert(0, str(HERMES_SOURCE))

_home = Path(tempfile.mkdtemp(prefix="scaleway-plugin-home-"))
_plugin = _home / "plugins" / "scaleway-provider"
_plugin.mkdir(parents=True)
shutil.copy(REPO_ROOT / "__init__.py", _plugin / "__init__.py")
shutil.copy(REPO_ROOT / "plugin.yaml", _plugin / "plugin.yaml")
os.environ["HERMES_HOME"] = str(_home)
