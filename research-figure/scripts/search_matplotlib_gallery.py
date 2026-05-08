#!/usr/bin/env python3
"""Search the bundled Matplotlib gallery index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_INDEX = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "figure"
    / "matplotlib-gallery-index.jsonl"
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
    values: list[str] = []
    for key in ("path", "category", "slug", "title", "summary", "gallery_url"):
        value = record.get(key)
        if value:
            values.append(str(value))
    for key in ("imports", "api_calls"):
        value = record.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return " ".join(values).lower()


def matches(record: dict[str, object], args: argparse.Namespace) -> bool:
    haystack = record_text(record)
    if args.query:
        terms = [term.lower() for term in args.query]
        if not all(term in haystack for term in terms):
            return False
    if args.category and str(record.get("category", "")).lower() != args.category.lower():
        return False
    if args.api:
        calls = [str(call).lower() for call in record.get("api_calls", [])]
        if not any(args.api.lower() in call for call in calls):
            return False
    return True


def format_record(record: dict[str, object], show_path: bool) -> str:
    calls = ", ".join(str(call) for call in record.get("api_calls", [])[:8])
    lines = [
        f"{record.get('title')} | {record.get('category')} | {record.get('slug')}",
        f"  gallery: {record.get('gallery_url')}",
    ]
    if show_path:
        lines.append(f"  path: {record.get('path')}")
    if record.get("summary"):
        lines.append(f"  summary: {record.get('summary')}")
    if calls:
        lines.append(f"  api: {calls}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--query", nargs="*", help="Terms that must all appear in the record.")
    parser.add_argument("--category", help="Filter by gallery category folder.")
    parser.add_argument("--api", help="Filter by detected API call substring.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--show-path", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    records = load_records(args.index)
    found = [record for record in records if matches(record, args)]
    for record in found[: args.limit]:
        print(format_record(record, args.show_path))
        print()
    print(f"{min(len(found), args.limit)} shown / {len(found)} matched / {len(records)} indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
