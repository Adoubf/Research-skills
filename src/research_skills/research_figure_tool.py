"""Console entry point for the bundled research-figure skill helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_tool_module():
    repo_root = Path(__file__).resolve().parents[2]
    tool_path = repo_root / "research-figure" / "scripts" / "research_figure_tool.py"
    spec = importlib.util.spec_from_file_location("_research_figure_tool", tool_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load tool module from {tool_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = _load_tool_module()
    return int(module.main())
