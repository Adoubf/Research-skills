#!/usr/bin/env python3
"""Search the bundled metadata-only Plottie reference index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_INDEX = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "figure"
    / "plottie-index.jsonl"
)


def load_records(index_path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with index_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def record_text(record: dict[str, object]) -> str:
    parts: list[str] = []
    for key in (
        "journal_name",
        "plot_type",
        "caption",
        "legend",
        "description",
        "seo_title",
    ):
        value = record.get(key)
        if value:
            parts.append(str(value))
    for key in ("tags", "visual_keywords", "context_keywords", "palette_hex"):
        value = record.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower()


def matches(record: dict[str, object], args: argparse.Namespace) -> bool:
    haystack = record_text(record)
    if args.query:
        terms = [term.lower() for term in args.query]
        if not all(term in haystack for term in terms):
            return False
    if args.plot_type and str(record.get("plot_type", "")).lower() != args.plot_type.lower():
        return False
    if args.journal and args.journal.lower() not in str(record.get("journal_name", "")).lower():
        return False
    return True


def format_record(record: dict[str, object], show_image_url: bool) -> str:
    tags = ", ".join(str(item) for item in record.get("visual_keywords", [])[:4])
    palette = ", ".join(str(item) for item in record.get("palette_hex", [])[:5])
    lines = [
        f"{record.get('id')} | {record.get('plot_type')} | {record.get('journal_name')}",
        f"  title: {record.get('seo_title')}",
        f"  doi: {record.get('doi')} | license: {record.get('license')}",
        f"  plottie: {record.get('plottie_url')}",
    ]
    if tags:
        lines.append(f"  visual: {tags}")
    if palette:
        lines.append(f"  palette: {palette}")
    if show_image_url:
        lines.append(f"  image: {record.get('image_url')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--query", nargs="*", help="Terms that must all appear in the record.")
    parser.add_argument("--plot-type", help="Filter by plot_type, such as bar, line, heatmap.")
    parser.add_argument("--journal", help="Filter by journal name substring.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-image-url", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    records = load_records(args.index)
    found = [record for record in records if matches(record, args)]
    for record in found[: args.limit]:
        print(format_record(record, args.show_image_url))
        print()
    print(f"{min(len(found), args.limit)} shown / {len(found)} matched / {len(records)} indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
