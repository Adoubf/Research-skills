# Plottie Reference Index

Use this reference only for visual inspiration and chart-pattern search. It is not a
source-data substitute and should not be copied into final figures.

## Source and license

- Source page: `https://plottie.art/gallery`
- License summary checked on 2026-05-08: Plottie states that scientific figures in
  the gallery come from open-access CC BY articles and can be shared/adapted with
  attribution.
- Terms constraint checked on 2026-05-08: Plottie prohibits automated bulk scraping,
  downloading, or extraction of substantial portions of the service.
- `robots.txt` checked on 2026-05-08: `/gallery` is allowed, `/api/` is disallowed,
  and Plottie notes that the API and image subdomains have separate robots policies.

This repository therefore stores a small metadata-only index from the public gallery
page. It does not bulk-download Plottie images. When a figure pattern is useful, open
the `plottie_url` and cite the original article DOI/license in any downstream work.

## Files

- `references/figure/plottie-index.jsonl`: searchable metadata records.
- `scripts/search_plottie_reference.py`: local search helper for the JSONL index.

## Search examples

```bash
python scripts/search_plottie_reference.py --query heatmap --limit 5
python scripts/search_plottie_reference.py --plot-type line --journal "Nature Materials"
python scripts/search_plottie_reference.py --query "single-cell dot plot" --show-image-url
```

## Record fields

Each JSONL record contains:

- `id`: Plottie plot id.
- `plottie_url`: public detail page.
- `image_url`: remote image URL for manual inspection; do not bulk download.
- `doi`: original article DOI inferred from the Plottie subplot path.
- `license`: Plottie-provided license string.
- `journal_name`, `plot_type`, `caption`, `legend`, `description`, `seo_title`.
- `tags`, `visual_keywords`, `context_keywords`, `palette_hex`.

## Usage boundary

Use the index to answer questions such as:

- "Find Nature-style dot plots with single-cell context."
- "Show me examples of effect-size or forest-plot layouts."
- "Which palettes appear in recent Nature Materials line plots?"

Do not use it to recreate a third-party figure wholesale. For final output, build a
new figure from the user's own source data and figure contract.
