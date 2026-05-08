---
name: research-figure
description: Create, reproduce, revise, and quality-check publication-grade scientific figures from user-provided source data and reference charts. Use when the task involves Nature-style figure making, chart replication, multi-panel figure layout, Python matplotlib code, R ggplot2/patchwork code, manuscript figure QA, or exporting editable SVG/PDF/TIFF figure assets. Requires an explicit source data directory for final plotted figures.
---

# Research Figure

Use this skill for scientific figure creation and chart reproduction. Work from the user's
claim, source data, and target output instead of starting from a favorite plotting template.

## Required Workflow

1. Establish the figure contract before writing plotting code.
   - Read `references/figure-contract.md`.
   - Capture the core conclusion, figure archetype, target output, final size, panel map,
     evidence hierarchy, statistics needs, source data needs, image-integrity notes, and reviewer risk.
   - If the user provides data but no claim, infer a provisional claim and ask for confirmation before final styling.

2. Require source data for final figures.
   - Final plotted figures must use an explicit user-provided data directory.
   - Do not silently estimate chart values from screenshots for a final figure.
   - If data is missing, produce only a data request, source-data template, or non-final draft plan.

3. Choose exactly one plotting backend.
   - Read `references/backend-selection.md` at the start of a figure task.
   - If the backend is not specified, ask the user to choose Python or R and stop until answered.
   - Once selected, use that backend for all plotting, preview rendering, visual QA, and final exports.
   - Do not render fallback previews with the non-selected backend.

4. Generate a self-contained plotting script.
   - For Python, use Matplotlib as the core backend and follow `references/api.md`,
     `references/common-patterns.md`, `references/chart-types.md`, and `references/tutorials.md`.
   - For R, follow `references/r-workflow.md`; use `ggplot2`, `patchwork`, and task-specific R packages.
   - Keep input paths configurable and avoid embedding private absolute paths in generated code.

5. Export editable publication assets.
   - SVG is the primary output for text-containing figures.
   - Also export PDF and TIFF/PNG previews when requested or when QA needs raster inspection.
   - Preserve editable text: Python must set `svg.fonttype = 'none'`; R should use `svglite` for SVG.

6. Run figure QA before delivery.
   - Read `references/qa-contract.md`.
   - Check backend exclusivity, final size, text readability, panel labels, editable text, statistics,
     source-data traceability, raster resolution, image integrity, and export bundle completeness.
   - When a project has been rendered, create or update `manifest.json` and run `validate-figure`.

## Reference Selection

- Use `references/figure-contract.md` for the task contract and panel logic.
- Use `references/backend-selection.md` before any plotting implementation.
- Use `references/design-theory.md` for Nature-style typography, layout, color, and composition rules.
- Use `references/nature-2026-observations.md` for 2026 Nature-family figure archetypes.
- Use `references/api.md` for Python constants, helper signatures, and mandatory rcParams.
- Use `references/common-patterns.md` for reusable Python layout and encoding patterns.
- Use `references/chart-types.md` for radar, 3D/conceptual, scatter, area, log-scale, and GridSpec patterns.
- Use `references/tutorials.md` for end-to-end Python examples.
- Use `references/r-workflow.md` for R implementation and export patterns.
- Use `references/r-template-index.md` only when the user chooses R and provides or mentions private R templates.
- Use `references/qa-contract.md` before final delivery or revision packages.
- Use `references/plottie-reference.md` only when searching for public visual inspiration from Plottie metadata.

## Privacy and Provenance

- Do not reveal private paths, source filenames, template identifiers, or private working materials unless the user explicitly asks.
- User-facing output should describe reused materials generically, such as "a grouped bar template" or "a heatmap workflow".
- Generated final scripts should use neutral comments and relative/configurable paths.

## Bundled Scripts

Use `scripts/research_figure_tool.py` from the installed skill root for deterministic
validation and packaging tasks. The script has no runtime dependency beyond Python.

```bash
python scripts/research_figure_tool.py validate-skill .
python scripts/research_figure_tool.py validate-project <project-dir>
python scripts/research_figure_tool.py validate-figure <project-dir>
python scripts/research_figure_tool.py pack-skill . --out dist
```

For Claude Code, run from `${CLAUDE_SKILL_DIR}` when that variable is available.
For repository development, the console helper is also available:

```bash
uv run research-figure-tool validate-skill research-figure
uv run research-figure-tool validate-figure examples/minimal-figure-project
uv run research-figure-tool pack-skill research-figure --out dist
```

The script validates project data directories, rendered figure QA metadata, export bundles, and skill package structure. It does not call any LLM API.

Use `scripts/search_plottie_reference.py` to search the bundled metadata-only Plottie
reference index:

```bash
python scripts/search_plottie_reference.py --query heatmap --limit 5
python scripts/search_plottie_reference.py --plot-type line --journal "Nature Materials"
```

The Plottie index stores links and metadata only. Do not bulk-download remote images.

## Figure Manifest for QA

For final figure projects, write `manifest.json` in the project root. Keep paths project-relative.
YAML manifests are intentionally not supported. The `validate-figure` command checks
this file against the figure contract and QA contract.

```json
{
  "backend": "python",
  "data_dir": "data",
  "script": "scripts/plot_figure.py",
  "exports": {
    "svg": "figures/figure.svg",
    "pdf": "figures/figure.pdf",
    "preview": "figures/figure.tiff"
  },
  "figure_contract": {
    "core_conclusion": "Treatment X reduces Y by restoring Z.",
    "figure_archetype": "quantitative grid",
    "target_journal_output": "Nature-family double-column figure",
    "backend": "Python",
    "final_size": "183 mm x 120 mm",
    "panel_map": {
      "a": "Primary comparison",
      "b": "Validation analysis"
    },
    "evidence_hierarchy": {
      "hero evidence": "Panel a",
      "validation evidence": "Panel b",
      "controls/robustness": "Source data and statistics notes"
    },
    "statistics_needed": "n, center, spread, test, correction",
    "source_data_needed": "data/source.csv",
    "image_integrity_notes": "No image panels",
    "reviewer_risk": "Axis comparability and sample-size visibility"
  },
  "qa": {
    "core_conclusion": "pass",
    "archetype": "pass",
    "backend_exclusivity": "pass",
    "final_size": "pass",
    "text_size": "pass",
    "panel_labels": "pass",
    "editable_text": "pass",
    "font": "pass",
    "color": "pass",
    "legend_strategy": "pass",
    "statistics": "pass",
    "source_data": "pass",
    "raster_resolution": "n/a",
    "microscopy_scale": "n/a",
    "image_integrity": "n/a",
    "export_bundle": "pass"
  },
  "statistical_claims": true,
  "statistics": {
    "n definition": "Biological replicates per group",
    "biological replicates": "n = 3 independent cultures",
    "technical replicates": "Two measurements per culture",
    "center statistic": "Mean",
    "spread/interval": "95% CI",
    "test": "Two-sided test",
    "multiple-comparison correction": "Benjamini-Hochberg",
    "p-value display": "Exact p values in source data",
    "source-data file": "data/source.csv"
  },
  "image_panels": false
}
```

`validate-figure` enforces the presence of `figure_contract`, all QA checks from
`references/qa-contract.md`, backend-matching script extensions, SVG primary export,
and backend-specific editable-text export settings.

Use `examples/minimal-figure-project/` in the repository as the reference structure
for a minimal valid `manifest.json`, source data directory, plotting script, and
SVG/PDF/TIFF export bundle.
