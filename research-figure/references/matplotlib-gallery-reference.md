# Matplotlib Gallery Reference Index

Use this reference when a Python figure task needs a known Matplotlib pattern,
API idiom, or official example to adapt. The bundled index is built from local
gallery source files under `references/code/matplotlib/`.

## Source and license

- Official gallery: `https://matplotlib.org/stable/gallery/`
- Official project license page checked on 2026-05-08:
  `https://matplotlib.org/stable/project/license.html`
- Matplotlib is distributed under a BSD-compatible license. Keep attribution when
  reusing substantial example code.

The code examples in this repository were provided by the user as local files.
The index stores metadata extracted from those local files; it does not scrape the
Matplotlib website.

## Files

- `references/code/matplotlib/`: local Matplotlib gallery `.py` examples.
- `references/figure/matplotlib-gallery-index.jsonl`: generated searchable index.
- `scripts/build_matplotlib_gallery_index.py`: rebuild the index from local code.
- `scripts/search_matplotlib_gallery.py`: search the generated index.

## Search examples

```bash
python scripts/search_matplotlib_gallery.py --query violin
python scripts/search_matplotlib_gallery.py --category statistics --limit 8
python scripts/search_matplotlib_gallery.py --api fill_between --show-path
```

## Record fields

Each JSONL record contains:

- `path`: path relative to the skill root.
- `category`: gallery category folder.
- `slug`: file stem.
- `title`: title parsed from the module docstring.
- `summary`: remaining docstring text, normalized.
- `imports`: top-level imported modules.
- `api_calls`: common Matplotlib/Pyplot/Axes calls detected from source.
- `gallery_url`: inferred official gallery URL for manual lookup.

## Usage boundary

Use these examples as implementation references, not as final style. For final
research figures, still apply the `research-figure` contract, selected backend,
publication rcParams, source-data traceability, and export QA rules.
