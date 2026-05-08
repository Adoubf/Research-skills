#!/usr/bin/env python3
"""Validation and packaging helper for the research-figure skill."""

from __future__ import annotations

import ast
import argparse
import fnmatch
import json
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

FIGURE_CONTRACT_FIELDS = {
    "core_conclusion": "Core conclusion",
    "figure_archetype": "Figure archetype",
    "target_journal_output": "Target journal/output",
    "backend": "Backend",
    "final_size": "Final size",
    "panel_map": "Panel map",
    "evidence_hierarchy": "Evidence hierarchy",
    "statistics_needed": "Statistics needed",
    "source_data_needed": "Source data needed",
    "image_integrity_notes": "Image-integrity notes",
    "reviewer_risk": "Reviewer risk",
}

ALLOWED_ARCHETYPES = {
    "quantitative grid",
    "schematic-led composite",
    "image plate + quant",
    "asymmetric mixed-modality figure",
}

QA_REQUIRED_PASS = {
    "core_conclusion": "Core conclusion",
    "archetype": "Archetype",
    "backend_exclusivity": "Backend exclusivity",
    "final_size": "Final size",
    "text_size": "Text size",
    "panel_labels": "Panel labels",
    "editable_text": "Editable text",
    "font": "Font",
    "color": "Color",
    "legend_strategy": "Legend strategy",
    "statistics": "Statistics",
    "source_data": "Source data",
    "export_bundle": "Export bundle",
}

QA_IMAGE_PANEL_FIELDS = {
    "raster_resolution": "Raster resolution",
    "microscopy_scale": "Microscopy scale",
    "image_integrity": "Image integrity",
}

STATS_REQUIRED_FIELDS = [
    "n definition",
    "biological replicates",
    "technical replicates",
    "center statistic",
    "spread/interval",
    "test",
    "multiple-comparison correction",
    "p-value display",
    "source-data file",
]

IMAGE_INTEGRITY_REQUIRED_FIELDS = [
    "raw file",
    "processed file",
    "crop",
    "brightness/contrast/gamma",
    "pseudo-color",
    "scale calibration",
    "stitching",
    "reuse in other figures",
    "quantification link",
]

PASS_VALUES = {"pass", "passed", "true", "yes", "ok", "done"}
NA_VALUES = {"n/a", "na", "not_applicable"}
BACKENDS = {"python", "r"}
SCRIPT_EXTENSIONS = {"python": {".py"}, "r": {".r"}}
VECTOR_EXPORT_EXTENSIONS = {".svg"}
SECONDARY_EXPORT_EXTENSIONS = {".pdf", ".tif", ".tiff", ".png"}
FINAL_SIZE_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mm|cm|in|px)\b", re.IGNORECASE)

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

    manifest_data: dict[str, object] | None = None
    manifest = project_dir / "manifest.json"
    has_yaml_manifest = (project_dir / "manifest.yaml").is_file() or (
        project_dir / "manifest.yml"
    ).is_file()
    if manifest.is_file():
        manifest_data = load_json_manifest(manifest, result)
        if manifest_data is not None:
            validate_manifest_data(manifest, manifest_data, result)
    elif has_yaml_manifest:
        result.errors.append("manifest.yaml/yml is not supported; use manifest.json")
    else:
        result.warnings.append(
            "No manifest found. Add manifest.json for reproducible figure tasks."
        )

    data_dir_value = None
    if isinstance(manifest_data, dict):
        data_dir_value = manifest_data.get("data_dir")
    data_dir = resolve_project_relative_path(
        project_dir, data_dir_value or "data", "manifest data_dir", result
    )
    data_dir_label = str(data_dir_value) if data_dir_value else "data/"
    if data_dir is None:
        return result
    if not data_dir.is_dir():
        result.errors.append(f"Missing required data directory: {data_dir_label}")
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

    return result


def load_json_manifest(manifest: Path, result: CheckResult) -> dict[str, object] | None:
    try:
        data = json.loads(read_text(manifest))
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON manifest: {manifest.name}: {exc}")
        return None
    if not isinstance(data, dict):
        result.errors.append(f"{manifest.name} must contain a JSON object")
        return None
    return data


def validate_manifest(manifest: Path, result: CheckResult) -> None:
    data = load_json_manifest(manifest, result)
    if data is None:
        return
    validate_manifest_data(manifest, data, result)


def validate_manifest_data(manifest: Path, data: dict[str, object], result: CheckResult) -> None:
    for key in ("backend", "data_dir"):
        if key not in data:
            result.warnings.append(f"{manifest.name} is missing recommended key: {key}")
    backend = data.get("backend")
    if backend is not None and normalize_backend(backend) not in BACKENDS:
        result.errors.append("manifest backend must be either 'python' or 'r'")
    data_dir = data.get("data_dir")
    if data_dir:
        resolved = resolve_project_relative_path(
            manifest.parent, data_dir, "manifest data_dir", result
        )
        if resolved is not None and not resolved.is_dir():
            result.errors.append(f"manifest data_dir does not exist: {data_dir}")


def validate_figure(project_dir: Path) -> CheckResult:
    project_dir = project_dir.resolve()
    result = validate_project(project_dir)
    manifest = project_dir / "manifest.json"
    if not manifest.is_file():
        result.errors.append("Figure validation requires manifest.json")
        return result

    data = load_json_manifest(manifest, result)
    if data is None:
        return result

    backend = normalize_backend(data.get("backend"))
    if backend not in BACKENDS:
        result.errors.append("Figure manifest must set backend to 'python' or 'r'")

    validate_figure_contract(data, backend, project_dir, result)
    validate_plot_script(project_dir, data, backend, result)
    validate_exports(project_dir, data, result)
    validate_qa_checklist(data, result)
    validate_source_data_references(project_dir, data, result)
    validate_conditional_qa_details(project_dir, data, result)
    return result


def validate_figure_contract(
    data: dict[str, object],
    backend: str | None,
    project_dir: Path,
    result: CheckResult,
) -> None:
    contract = data.get("figure_contract") or data.get("contract")
    if not isinstance(contract, dict):
        result.errors.append("manifest must include a figure_contract object")
        return
    for key, label in FIGURE_CONTRACT_FIELDS.items():
        value = contract.get(key)
        if is_blank(value):
            result.errors.append(f"figure_contract missing required field: {key} ({label})")
    panel_map = contract.get("panel_map")
    if not isinstance(panel_map, dict) or not panel_map:
        result.errors.append("figure_contract.panel_map must be a non-empty object")
    evidence = contract.get("evidence_hierarchy")
    if not isinstance(evidence, dict) or not evidence:
        result.errors.append("figure_contract.evidence_hierarchy must be a non-empty object")
    archetype = contract.get("figure_archetype")
    if not is_blank(archetype):
        normalized_archetype = normalize_text(archetype)
        if normalized_archetype not in ALLOWED_ARCHETYPES:
            allowed = ", ".join(sorted(ALLOWED_ARCHETYPES))
            result.errors.append(
                f"figure_contract.figure_archetype must be one of: {allowed}"
            )
    contract_backend = normalize_backend(contract.get("backend"))
    if contract_backend and backend in BACKENDS and contract_backend != backend:
        result.errors.append(
            "figure_contract.backend must match manifest backend "
            f"({contract_backend!r} != {backend!r})"
        )
    final_size = contract.get("final_size")
    if not is_blank(final_size) and not is_valid_final_size(final_size):
        result.errors.append(
            "figure_contract.final_size must include numeric dimensions with units "
            "(mm, cm, in, or px)"
        )


def validate_plot_script(
    project_dir: Path,
    data: dict[str, object],
    backend: str | None,
    result: CheckResult,
) -> None:
    script_value = data.get("script") or data.get("plot_script")
    if is_blank(script_value):
        result.errors.append("manifest must include script or plot_script")
        return

    script_path = resolve_project_relative_path(
        project_dir, script_value, "manifest script", result
    )
    if script_path is None:
        return
    if not script_path.is_file():
        result.errors.append(f"plot script does not exist: {script_value}")
        return

    if backend in SCRIPT_EXTENSIONS:
        suffix = script_path.suffix.lower()
        if suffix not in SCRIPT_EXTENSIONS[backend]:
            expected = ", ".join(sorted(SCRIPT_EXTENSIONS[backend]))
            result.errors.append(
                f"plot script extension {script_path.suffix!r} does not match backend {backend}; expected {expected}"
            )

    text = read_text(script_path)
    if backend == "python":
        python_checks = inspect_python_plot_script(script_path, text, result)
        if not python_checks["svg_fonttype_none"]:
            result.errors.append("Python plot script must set svg.fonttype='none' for editable SVG text")
        if not python_checks["pdf_fonttype_42"]:
            result.warnings.append("Python plot script should set pdf.fonttype=42 for editable PDF text")
        if not python_checks["savefig"]:
            result.warnings.append("Python plot script does not appear to save figure outputs with savefig")
    elif backend == "r":
        r_checks = inspect_r_plot_script(text)
        if not r_checks["svglite"]:
            result.errors.append("R plot script must use svglite for editable SVG export")
        if not r_checks["cairo_pdf"]:
            result.errors.append("R plot script must export PDF with grDevices::cairo_pdf")
        if not r_checks["agg_tiff"]:
            result.errors.append("R plot script must export TIFF preview with ragg::agg_tiff")


def validate_exports(project_dir: Path, data: dict[str, object], result: CheckResult) -> None:
    export_values = flatten_exports(data.get("exports") or data.get("output_files"))
    if not export_values:
        result.errors.append("manifest must include exports or output_files")
        return

    existing_suffixes: set[str] = set()
    for value in export_values:
        export_path = resolve_project_relative_path(project_dir, value, "export path", result)
        if export_path is None:
            continue
        suffix = export_path.suffix.lower()
        if not export_path.is_file():
            result.errors.append(f"listed export does not exist: {value}")
            continue
        existing_suffixes.add(suffix)
        if suffix == ".svg":
            inspect_svg_export(export_path, result)

    if not existing_suffixes.intersection(VECTOR_EXPORT_EXTENSIONS):
        result.errors.append("export bundle must include an SVG primary output")
    if ".pdf" not in existing_suffixes:
        result.warnings.append("export bundle should include a PDF output")
    if not existing_suffixes.intersection({".tif", ".tiff", ".png"}):
        result.warnings.append("export bundle should include a TIFF or PNG preview")


def inspect_svg_export(svg_path: Path, result: CheckResult) -> None:
    text = read_text(svg_path)
    if "<text" not in text:
        result.warnings.append(f"SVG has no <text> nodes; verify text was not outlined: {svg_path.name}")
    if "<svg" not in text:
        result.errors.append(f"SVG export does not look like an SVG file: {svg_path.name}")


def validate_qa_checklist(data: dict[str, object], result: CheckResult) -> None:
    qa = data.get("qa")
    if not isinstance(qa, dict):
        result.errors.append("manifest must include a qa object based on references/qa-contract.md")
        return
    for key, label in QA_REQUIRED_PASS.items():
        if key not in qa:
            result.errors.append(f"qa missing required check: {key} ({label})")
            continue
        if not is_pass_value(qa[key]):
            result.errors.append(f"qa check did not pass: {key} ({label})")
    has_image_panels = truthy(data.get("image_panels"))
    for key, label in QA_IMAGE_PANEL_FIELDS.items():
        if key not in qa:
            result.errors.append(f"qa missing required check: {key} ({label})")
            continue
        if has_image_panels:
            if not is_pass_value(qa[key]):
                result.errors.append(f"image-panel qa check did not pass: {key} ({label})")
        elif not (is_pass_value(qa[key]) or is_na_value(qa[key])):
            result.errors.append(
                f"qa check must be pass or n/a when image_panels=false: {key} ({label})"
            )


def validate_source_data_references(
    project_dir: Path, data: dict[str, object], result: CheckResult
) -> None:
    contract = data.get("figure_contract") or data.get("contract")
    if not isinstance(contract, dict):
        return
    validate_source_data_value(
        project_dir,
        contract.get("source_data_needed"),
        "figure_contract.source_data_needed",
        result,
    )


def validate_conditional_qa_details(
    project_dir: Path, data: dict[str, object], result: CheckResult
) -> None:
    if truthy(data.get("statistical_claims")):
        statistics = data.get("statistics")
        if not isinstance(statistics, dict):
            result.errors.append("statistical_claims=true requires a statistics object")
        else:
            for field in STATS_REQUIRED_FIELDS:
                if is_blank(statistics.get(field)):
                    result.errors.append(f"statistics missing required field: {field}")
            validate_source_data_value(
                project_dir,
                statistics.get("source-data file"),
                "statistics.source-data file",
                result,
            )
    if truthy(data.get("image_panels")):
        image_integrity = data.get("image_integrity")
        if not isinstance(image_integrity, dict):
            result.errors.append("image_panels=true requires an image_integrity object")
        else:
            for field in IMAGE_INTEGRITY_REQUIRED_FIELDS:
                if is_blank(image_integrity.get(field)):
                    result.errors.append(f"image_integrity missing required field: {field}")
            for field in ("raw file", "processed file", "quantification link"):
                value = image_integrity.get(field)
                if not is_blank(value) and not is_na_value(value):
                    validate_project_file_reference(
                        project_dir, value, f"image_integrity.{field}", result
                    )


def normalize_backend(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def normalize_text(value: object) -> str:
    return str(value).strip().lower()


def is_valid_final_size(value: object) -> bool:
    return len(FINAL_SIZE_RE.findall(str(value))) >= 2


def resolve_project_path(project_dir: Path, value: object) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path.resolve()
    return (project_dir / path).resolve()


def resolve_project_relative_path(
    project_dir: Path, value: object, label: str, result: CheckResult
) -> Path | None:
    if is_blank(value):
        result.errors.append(f"{label} is blank")
        return None
    raw = str(value).strip()
    path = Path(raw)
    if path.is_absolute():
        result.errors.append(f"{label} must be project-relative, not absolute: {raw}")
        return None
    resolved = (project_dir / path).resolve()
    if not is_within(resolved, project_dir):
        result.errors.append(f"{label} escapes project directory: {raw}")
        return None
    return resolved


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def validate_source_data_value(
    project_dir: Path,
    value: object,
    label: str,
    result: CheckResult,
) -> None:
    if is_blank(value):
        result.errors.append(f"{label} must reference at least one source-data file")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_project_data_file_reference(
                project_dir, item, f"{label}[{index}]", result
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_project_data_file_reference(
                project_dir, item, f"{label}.{key}", result
            )
        return
    validate_project_data_file_reference(project_dir, value, label, result)


def validate_project_data_file_reference(
    project_dir: Path, value: object, label: str, result: CheckResult
) -> None:
    path = validate_project_file_reference(project_dir, value, label, result)
    if path is None:
        return
    if path.suffix.lower() not in DATA_EXTENSIONS:
        allowed = ", ".join(sorted(DATA_EXTENSIONS))
        result.errors.append(f"{label} has unsupported source-data extension: {path.suffix}; expected {allowed}")


def validate_project_file_reference(
    project_dir: Path, value: object, label: str, result: CheckResult
) -> Path | None:
    path = resolve_project_relative_path(project_dir, value, label, result)
    if path is None:
        return None
    if not path.is_file():
        result.errors.append(f"{label} does not exist: {value}")
        return None
    return path


def inspect_python_plot_script(
    script_path: Path, text: str, result: CheckResult
) -> dict[str, bool]:
    checks = {"svg_fonttype_none": False, "pdf_fonttype_42": False, "savefig": False}
    try:
        tree = ast.parse(text, filename=str(script_path))
    except SyntaxError as exc:
        result.errors.append(f"Python plot script has syntax error: {exc}")
        return checks

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                update_rcparam_check(target, node.value, checks)
        elif isinstance(node, ast.Call):
            if is_savefig_call(node):
                checks["savefig"] = True
            update_rcparams_update_check(node, checks)
    return checks


def update_rcparam_check(
    target: ast.expr, value_node: ast.AST, checks: dict[str, bool]
) -> None:
    key = rcparams_subscript_key(target)
    if key == "svg.fonttype" and literal_value(value_node) == "none":
        checks["svg_fonttype_none"] = True
    if key == "pdf.fonttype" and literal_value(value_node) in {42, "42"}:
        checks["pdf_fonttype_42"] = True


def update_rcparams_update_check(node: ast.Call, checks: dict[str, bool]) -> None:
    if not (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "update"
        and is_rcparams_object(node.func.value)
    ):
        return
    if not node.args:
        return
    mapping = literal_value(node.args[0])
    if not isinstance(mapping, dict):
        return
    if mapping.get("svg.fonttype") == "none":
        checks["svg_fonttype_none"] = True
    if mapping.get("pdf.fonttype") in {42, "42"}:
        checks["pdf_fonttype_42"] = True


def rcparams_subscript_key(target: ast.expr) -> str | None:
    if not isinstance(target, ast.Subscript) or not is_rcparams_object(target.value):
        return None
    key = literal_value(target.slice)
    if isinstance(key, str):
        return key
    return None


def is_rcparams_object(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "rcParams"
        and dotted_name(node.value) in {"plt", "mpl", "matplotlib"}
    )


def is_savefig_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute) and node.func.attr == "savefig":
        return True
    return isinstance(node.func, ast.Name) and node.func.id == "savefig"


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        if prefix:
            return f"{prefix}.{node.attr}"
    return None


def literal_value(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def inspect_r_plot_script(text: str) -> dict[str, bool]:
    cleaned = strip_r_comments(text)
    return {
        "svglite": bool(re.search(r"\b(?:svglite::)?svglite\s*\(", cleaned)),
        "cairo_pdf": bool(re.search(r"\b(?:grDevices::)?cairo_pdf\s*\(", cleaned)),
        "agg_tiff": bool(re.search(r"\b(?:ragg::)?agg_tiff\s*\(", cleaned)),
    }


def strip_r_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        in_single = False
        in_double = False
        escaped = False
        kept: list[str] = []
        for char in line:
            if escaped:
                kept.append(char)
                escaped = False
                continue
            if char == "\\":
                kept.append(char)
                escaped = True
                continue
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            if char == "#" and not in_single and not in_double:
                break
            kept.append(char)
        lines.append("".join(kept))
    return "\n".join(lines)


def is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "1", "y"}


def is_pass_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower().replace("-", "_").replace(" ", "_") in PASS_VALUES


def is_na_value(value: object) -> bool:
    if value is None:
        return False
    return str(value).strip().lower().replace("-", "_").replace(" ", "_") in NA_VALUES


def flatten_exports(exports: object) -> list[object]:
    if exports is None:
        return []
    if isinstance(exports, dict):
        values: list[object] = []
        for value in exports.values():
            if isinstance(value, list):
                values.extend(value)
            else:
                values.append(value)
        return [value for value in values if not is_blank(value)]
    if isinstance(exports, list):
        return [value for value in exports if not is_blank(value)]
    return [exports] if not is_blank(exports) else []


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
    shutil.copytree(skill_dir, package_dir, ignore=make_copy_ignore({out_dir}))
    copy_license_into_package(skill_dir, package_dir)

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


def make_copy_ignore(skip_dirs: set[Path]):
    resolved_skip_dirs = {path.resolve() for path in skip_dirs}

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = copy_ignore(directory, names)
        directory_path = Path(directory).resolve()
        for name in names:
            candidate = (directory_path / name).resolve()
            if any(candidate == skip_dir for skip_dir in resolved_skip_dirs):
                ignored.add(name)
        return ignored

    return ignore


def copy_license_into_package(skill_dir: Path, package_dir: Path) -> None:
    for candidate in (skill_dir / "LICENSE", skill_dir.parent / "LICENSE"):
        if candidate.is_file():
            shutil.copy2(candidate, package_dir / "LICENSE")
            return


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

    validate_figure_parser = subparsers.add_parser(
        "validate-figure", help="Validate a rendered figure project against the QA contract."
    )
    validate_figure_parser.add_argument("project_dir", type=Path)

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
    if args.command == "validate-figure":
        result = validate_figure(args.project_dir)
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
