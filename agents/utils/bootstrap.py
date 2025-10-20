from __future__ import annotations
import sys
import types
import re
import importlib.util
from pathlib import Path

"""Utilities for dynamically exposing the analyzer-helpers directory as the
package name `analyzer_helpers` so imports work across modules.
"""


def bootstrap_analyzer_helpers(base_dir: Path) -> None:
    candidates = [
        base_dir / "analyzer-helpers",
        base_dir.parent
        / "incident-analyzer-hackathon"
        / "incident-analyzer"
        / "analyzer-helpers",
    ]
    base = None
    for c in candidates:
        if c.exists():
            base = c
            break
    if base is None:
        return

    pkg_name = "analyzer_helpers"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(base)]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg
    else:
        pkg = sys.modules[pkg_name]

    for py in base.glob("*.py"):
        if not py.is_file():
            continue
        stem = py.stem
        mod_name = re.sub(r"[^0-9a-zA-Z_]", "_", stem)
        fqmn = f"{pkg_name}.{mod_name}"
        if fqmn in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(fqmn, py)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[fqmn] = mod
            spec.loader.exec_module(mod)
            setattr(pkg, mod_name, mod)
