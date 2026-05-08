#!/usr/bin/env python3
"""Build a searchable index for local Matplotlib gallery source files."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = SKILL_ROOT / "references" / "code" / "matplotlib"
DEFAULT_OUT = SKILL_ROOT / "references" / "figure" / "matplotlib-gallery-index.jsonl"

API_PREFIXES = {"plt", "ax", "axs", "fig", "np", "matplotlib"}


def parse_docstring(source: str) -> tuple[str, str]:
    try:
        module = ast.parse(source)
    except SyntaxError:
        return "", ""
    docstring = ast.get_docstring(module) or ""
    lines = [line.rstrip() for line in docstring.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    title = ""
    title_index = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if set(stripped) <= {"=", "-", "~", "^", "#", "*"}:
            continue
        title = stripped
        title_index = index
        break
    body_start = title_index + 1
    while body_start < len(lines):
        stripped = lines[body_start].strip()
        if not stripped or set(stripped) <= {"=", "-", "~", "^", "#", "*"}:
            body_start += 1
            continue
        break
    summary = normalize_text("\n".join(lines[body_start:]))
    return title, summary


def normalize_text(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r":(?:mod|class|func|meth|attr):`([^`]+)`", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def collect_imports(tree: ast.AST) -> list[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return sorted(imports)


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def collect_api_calls(tree: ast.AST) -> list[str]:
    calls: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)
        if not name or "." not in name:
            continue
        root = name.split(".", 1)[0]
        if root in API_PREFIXES:
            calls.add(name)
    return sorted(calls)


def gallery_url(relative_path: Path) -> str:
    return "https://matplotlib.org/stable/gallery/" + relative_path.with_suffix(".html").as_posix()


def build_record(path: Path, source_dir: Path, skill_root: Path) -> dict[str, object]:
    source = path.read_text(encoding="utf-8", errors="ignore")
    title, summary = parse_docstring(source)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = ast.Module(body=[], type_ignores=[])
    relative_source = path.relative_to(source_dir)
    return {
        "path": path.relative_to(skill_root).as_posix(),
        "category": relative_source.parts[0] if len(relative_source.parts) > 1 else "",
        "slug": path.stem,
        "title": title or path.stem.replace("_", " ").title(),
        "summary": summary,
        "imports": collect_imports(tree),
        "api_calls": collect_api_calls(tree),
        "gallery_url": gallery_url(relative_source),
    }


def build_index(source_dir: Path, out_path: Path, skill_root: Path) -> int:
    records = [
        build_record(path, source_dir, skill_root)
        for path in sorted(source_dir.rglob("*.py"))
        if path.is_file()
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    count = build_index(args.source.resolve(), args.out.resolve(), SKILL_ROOT.resolve())
    print(f"indexed {count} Matplotlib gallery examples -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
