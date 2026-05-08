# Nature Figure Design Theory

Use this file to make design decisions before choosing a concrete code pattern.
For Python helper code, read `api.md`. For layout snippets, read `common-patterns.md`.

## Typography

Nature-style scientific figures need small, stable, editable text at final size.

| Context | Typical final text | Axes linewidth |
|---|---:|---:|
| Dense journal-width composite | 7-9 pt | 0.8-1.2 |
| Compact analytic panel | 10-15 pt | 1.2-2.0 |
| Slide-scale comparison bar page | 20-24 pt | 2.0-3.0 |

Rules:

- Use a sans-serif stack: Arial first, then DejaVu Sans or Liberation Sans fallback.
- Keep SVG text editable with `svg.fonttype = "none"` and PDF text editable with `pdf.fonttype = 42`.
- Use lowercase bold panel labels near the top-left edge.
- Do not use slide-scale fonts in final manuscript figures unless the canvas is intentionally slide-scale.

## Axes and Legends

Keep charts quiet unless an axis or guide carries scientific meaning.

- Turn off top and right spines by default.
- Avoid grids unless the reader needs exact lookup.
- Use sparse ticks and direct labels where possible.
- Use frameless legends.
- Prefer one shared legend strip or dedicated legend axis over repeated legends.
- Hide categorical x ticks only when categories are already named by a legend, direct labels, or panel title.

## Color Strategy

Choose color from figure semantics, not from variety.

- Use one neutral family, one signal family, and one accent family.
- Keep the same condition, method, group, or biological state color across all panels.
- Prefer family-consistent palettes for related model or method variants.
- Reserve green/red for signed deltas, warnings, thresholds, or biological direction.
- Avoid rainbow palettes unless categories are intrinsic physical phases and directly labeled.
- Ensure grayscale print remains interpretable with hatches, labels, or luminance separation.

Modality guidance:

- Imaging plates: black image cells, grayscale context, one or two fluorescent channels.
- Schematic/material figures: derive colors from the physical or conceptual components, then reuse softened versions in support plots.
- Clinical composites: dark baseline/reference series, restrained follow-up hues, pale group bands.
- Genomics/systems figures: neutral scaffold plus a small number of biologically meaningful highlight families.

## Layout Strategy

Start from the evidence hierarchy in `figure-contract.md`.

| Archetype | Use when | Design signal |
|---|---|---|
| Quantitative grid | Claim is mainly numerical comparison | Shared axes, compact legends, aligned panels |
| Schematic-led composite | Mechanism, workflow, or device must be understood first | Large top/left schematic with smaller validation plots |
| Image plate + quant | Images lead the evidence | Dark or neutral image plate plus adjacent quantification |
| Clinical triptych | Longitudinal, effect-size, and summary evidence coexist | Parallel columns and consistent row logic |
| Asymmetric hero layout | One panel carries central evidence | Hero panel spans rows or columns |

Rules:

- Do not force equal panel sizes when evidence value is unequal.
- Give the hero panel enough area to carry the argument.
- Keep support panels visually quieter than the primary evidence.
- Increase gutters when dark image plates touch light chart panels.
- Use whitespace and alignment instead of decorative boxes.

## Chart-Specific Decisions

Bar charts:

- Use grouped bars for direct method/category comparison.
- Use horizontal bars for ablations or long labels.
- Use alpha progression only for variants of one method.
- Tighten y limits when the range is narrow, unless zero is scientifically necessary.
- Show error bars only when the statistic and replicate definition are documented.

Trends:

- Use shared legends for repeated line identities.
- Use low-alpha uncertainty bands.
- Keep event annotations sparse; move dense event information to a separate timeline panel.

Heatmaps:

- Use heatmaps for matrix structure, not as a decorative replacement for simple bars.
- Normalize by the comparison that matches the claim: global, per-row, per-column, or z-score.
- Use diverging maps only when there is a meaningful center.
- For biologically rich annotations, consider R/ComplexHeatmap.

Image plates:

- Use scale bars, not magnification-only labels.
- Keep crop geometry consistent across comparable cells.
- Document crop, contrast, pseudo-color, stitching, and raw-file traceability in QA notes.
- Quantify representative images when they support a claim.

## Anti-Redundancy

Every panel must answer a unique scientific question. If removing a panel would
not weaken the argument, merge or remove it.

Common traps:

| Trap | Fix |
|---|---|
| Absolute composition plus another absolute composition panel | Make the second panel deviation, z-score, or relationship |
| Parent cohort plus one subset shown the same way | Replace subset chart with a relationship or mechanism panel |
| Two ranked bars on related metrics | Replace one with scatter, bubble, or paired change plot |
| Pie chart plus stacked bar | Use one composition view and save space |

Useful progression:

1. Landscape: what is the overall composition or pattern?
2. Deviation: what is distinctive per group?
3. Relationship: how do variables co-vary?
4. Robustness: does the claim survive controls or subgroups?

## Export Policy

Use `api.md`'s required Matplotlib setup and `save_publication_figure()` helper.

Final Python figures should export:

- SVG primary output with editable text.
- PDF secondary vector output with editable text.
- TIFF or PNG preview for raster inspection and submission portals.

Do not use PNG as the only final output when the figure contains text.

## Reproduction Checklist

- Figure contract exists and every panel maps to the core conclusion.
- Selected backend produced all plotting, previews, exports, and visual QA renders.
- Text remains editable in SVG/PDF.
- Panel labels are lowercase, bold, and consistently placed.
- Font size is readable at final target dimensions.
- Colors are semantic and stable across panels.
- Legends are shared, direct, or omitted intentionally.
- Axis ranges match the scientific comparison.
- Statistics include `n`, replicate definition, center, spread, test, correction, and exact comparison.
- Source data and exported files are listed in `manifest.json`.
- `validate-figure <project-dir>` passes before final delivery.
