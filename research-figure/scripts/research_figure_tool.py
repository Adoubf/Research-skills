#!/usr/bin/env python3
"""Validation and packaging helper for the research-figure skill."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_REFERENCES = [
    "figure-contract.md",
    "backend-selection.md",
    "api.md",
    "common-patterns.md",
    "chart-types.md",
    "tutorials.md",
    "design-theory.md",
    "nature-2026-observations.md",
    "qa-contract.md",
    "r-workflow.md",
    "r-template-index.md",
]

DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".txt",
    ".xlsx",
    ".xls",
    ".json",
    ".jsonl",
    ".parquet",
    ".feather",
    ".rds",
    ".rda",
    ".rdata",
    ".npy",
    ".npz",
}

EXCLUDED_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


@dataclass
class CheckResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "CheckResult") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    raw = text[4:end].strip()
    metadata: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def validate_skill(skill_dir: Path) -> CheckResult:
    skill_dir = skill_dir.resolve()
    result = CheckResult(errors=[], warnings=[])

    skill_md = skill_dir / "SKILL.md"
    references_dir = skill_dir / "references"
    scripts_dir = skill_dir / "scripts"

    if not skill_md.is_file():
        result.errors.append(f"Missing required file: {rel(skill_md, skill_dir)}")
        return result

    text = read_text(skill_md)
    metadata = parse_frontmatter(text)
    if metadata.get("name") != skill_dir.name:
        result.errors.append(
            f"SKILL.md frontmatter name must match directory name '{skill_dir.name}'"
        )
    if not metadata.get("description"):
        result.errors.append("SKILL.md frontmatter must include a non-empty description")
    if len(metadata) > 2:
        extra = ", ".join(sorted(set(metadata) - {"name", "description"}))
        result.warnings.append(f"SKILL.md has non-portable frontmatter fields: {extra}")

    if not references_dir.is_dir():
        result.errors.append("Missing references directory")
    else:
        for name in REQUIRED_REFERENCES:
            if not (references_dir / name).is_file():
                result.errors.append(f"Missing reference file: references/{name}")

    if not scripts_dir.is_dir():
        result.errors.append("Missing scripts directory")
    elif not (scripts_dir / "research_figure_tool.py").is_file():
        result.errors.append("Missing script: scripts/research_figure_tool.py")

    missing_links = find_missing_reference_links(skill_dir)
    result.errors.extend(missing_links)
    return result


def find_missing_reference_links(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)#][^)]*)\)")
    for markdown_path in sorted(skill_dir.rglob("*.md")):
        text = read_text(markdown_path)
        for match in link_re.finditer(text):
            target = match.group(1).strip()
            if "://" in target or target.startswith("mailto:"):
                continue
            target_path = (markdown_path.parent / target).resolve()
            if not target_path.exists():
                errors.append(
                    f"Broken markdown link in {rel(markdown_path, skill_dir)}: {target}"
                )
    return errors


def validate_project(project_dir: Path) -> CheckResult:
    project_dir = project_dir.resolve()
    result = CheckResult(errors=[], warnings=[])

    if not project_dir.is_dir():
        result.errors.append(f"Project directory does not exist: {project_dir}")
        return result

    data_dir = project_dir / "data"
    if not data_dir.is_dir():
        result.errors.append("Missing required data directory: data/")
    else:
        data_files = [
            p
            for p in data_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in DATA_EXTENSIONS
        ]
        if not data_files:
            result.errors.append(
                "data/ exists but contains no supported source-data files "
                f"({', '.join(sorted(DATA_EXTENSIONS))})"
            )

    manifest = project_dir / "manifest.json"
    if manifest.is_file():
        validate_manifest(manifest, result)
    elif not (project_dir / "manifest.yaml").is_file() and not (project_dir / "manifest.yml").is_file():
        result.warnings.append(
            "No manifest found. Add manifest.json, manifest.yaml, or manifest.yml for reproducible figure tasks."
        )

    return result


def validate_manifest(manifest: Path, result: CheckResult) -> None:
    try:
        data = json.loads(read_text(manifest))
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON manifest: {manifest.name}: {exc}")
        return
    if not isinstance(data, dict):
        result.errors.append(f"{manifest.name} must contain a JSON object")
        return
    for key in ("backend", "data_dir"):
        if key not in data:
            result.warnings.append(f"{manifest.name} is missing recommended key: {key}")
    backend = data.get("backend")
    if backend is not None and backend not in {"python", "r", "Python", "R"}:
        result.errors.append("manifest backend must be either 'python' or 'r'")
    data_dir = data.get("data_dir")
    if data_dir:
        resolved = (manifest.parent / str(data_dir)).resolve()
        if not resolved.is_dir():
            result.errors.append(f"manifest data_dir does not exist: {data_dir}")


def pack_skill(skill_dir: Path, out_dir: Path, zip_output: bool = True) -> Path:
    skill_dir = skill_dir.resolve()
    out_dir = out_dir.resolve()
    result = validate_skill(skill_dir)
    if not result.ok:
        print_result(result)
        raise SystemExit(1)

    package_dir = out_dir / skill_dir.name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_dir, package_dir, ignore=copy_ignore)

    if zip_output:
        zip_path = out_dir / f"{skill_dir.name}.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(package_dir.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(out_dir))
        return zip_path
    return package_dir


def copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    patterns = ["*.pyc", "*.pyo", "*.tmp", "*.log"]
    for name in names:
        if name in EXCLUDED_NAMES:
            ignored.add(name)
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
            ignored.add(name)
    return ignored


def print_result(result: CheckResult) -> None:
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    if result.ok:
        print("ok")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and package the research-figure skill."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_skill_parser = subparsers.add_parser(
        "validate-skill", help="Validate a skill directory."
    )
    validate_skill_parser.add_argument("skill_dir", type=Path)

    validate_project_parser = subparsers.add_parser(
        "validate-project", help="Validate a figure project directory."
    )
    validate_project_parser.add_argument("project_dir", type=Path)

    pack_parser = subparsers.add_parser("pack-skill", help="Copy and zip a skill package.")
    pack_parser.add_argument("skill_dir", type=Path)
    pack_parser.add_argument("--out", type=Path, default=Path("dist"))
    pack_parser.add_argument("--no-zip", action="store_true", help="Only copy the skill directory.")

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "validate-skill":
        result = validate_skill(args.skill_dir)
        print_result(result)
        return 0 if result.ok else 1
    if args.command == "validate-project":
        result = validate_project(args.project_dir)
        print_result(result)
        return 0 if result.ok else 1
    if args.command == "pack-skill":
        output = pack_skill(args.skill_dir, args.out, zip_output=not args.no_zip)
        print(output)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
