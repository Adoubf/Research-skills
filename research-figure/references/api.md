# Python API Reference - Nature Figure Making

Use this file only after the user has selected Python as the plotting backend.
It provides copy-adaptable Matplotlib constants and helper patterns. Keep the
final script self-contained; do not import from this Markdown file.

## Required Matplotlib Setup

Place this block before creating any figure:

```python
import matplotlib
matplotlib.use("Agg")  # batch-safe; remove only for interactive notebooks

import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"  # editable SVG text
plt.rcParams["pdf.fonttype"] = 42      # editable TrueType text in PDF
```

SVG is the primary output for text-containing figures. Export PDF and TIFF/PNG
as secondary deliverables when the figure is final or needs QA.

## Palettes

```python
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "neutral_black": "#272727",
    "gold": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "magenta": "#EA84DD",
}

DEFAULT_COLORS = [
    PALETTE["blue_main"],
    PALETTE["green_3"],
    PALETTE["red_strong"],
    PALETTE["teal"],
    PALETTE["violet"],
    PALETTE["neutral_light"],
]

PALETTE_NMI_PASTEL = {
    "baseline_dark": "#484878",
    "baseline_mid": "#7884B4",
    "baseline_soft": "#B4C0E4",
    "ours_tiny": "#E4E4F0",
    "ours_base": "#E4CCD8",
    "ours_large": "#F0C0CC",
    "bg_lilac": "#E0E0F0",
    "bg_aqua": "#E0F0F0",
    "bg_peach": "#F0E0D0",
    "neutral_light": "#D8D8D8",
    "neutral_mid": "#A8A8A8",
    "neutral_dark": "#606060",
    "delta_up": "#2E9E44",
    "delta_down": "#E53935",
}

DEFAULT_COLORS_NMI_PASTEL = [
    PALETTE_NMI_PASTEL["baseline_dark"],
    PALETTE_NMI_PASTEL["baseline_mid"],
    PALETTE_NMI_PASTEL["baseline_soft"],
    PALETTE_NMI_PASTEL["ours_tiny"],
    PALETTE_NMI_PASTEL["ours_base"],
    PALETTE_NMI_PASTEL["ours_large"],
]

PALETTE_NATURE_IMAGING = {
    "bg": "#000000",
    "context": "#B8B8B8",
    "cyan": "#22D7E6",
    "magenta": "#FF2AD4",
    "white": "#FFFFFF",
}

PALETTE_NATURE_MATERIAL = {
    "aqua": "#77D7D1",
    "teal": "#33B5A5",
    "lilac": "#B9A7E8",
    "violet": "#7C6CCF",
    "callout_red": "#E53935",
    "neutral": "#D9D9D9",
}

PALETTE_NATURE_CLINICAL = {
    "baseline": "#272727",
    "week6": "#E28E2C",
    "week13": "#D24B40",
    "week26": "#5B8FD6",
    "year1": "#7BAA5B",
    "year2": "#C45AD6",
    "group_band": "#F2E6D9",
}

PALETTE_NATURE_GENOMICS = {
    "neutral_light": "#D8D8D8",
    "neutral_mid": "#8F8F8F",
    "wave1": "#D9544D",
    "wave2": "#5B7FCA",
    "wave3": "#B89BD9",
    "outline": "#4D4D4D",
}
```

Use `DEFAULT_COLORS` when categories have distinct semantic roles. Use
`DEFAULT_COLORS_NMI_PASTEL` when multiple compared methods belong to related
families and the page should read as one coherent figure.

## Core Helpers

```python
def apply_publication_style(font_size=8, axes_linewidth=1.0, use_tex=False):
    """Apply Nature-style rcParams. Call once before creating figures."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.size"] = font_size
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.linewidth"] = axes_linewidth
    plt.rcParams["legend.frameon"] = False
    if use_tex:
        plt.rcParams["text.usetex"] = True
```

Presets:

- Dense journal-width composite: `font_size=8, axes_linewidth=1.0`
- Compact analytic plot: `font_size=15, axes_linewidth=2.0`
- Large comparison bar page: `font_size=24, axes_linewidth=3.0`

```python
def is_dark(hex_color, threshold=128):
    """Return True when white text is safer on the color."""
    c = hex_color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) < threshold


def add_panel_label(ax, label, x=-0.06, y=1.02, fontsize=8,
                    color="black", fontweight="bold"):
    """Place a Nature-style lowercase panel label."""
    ax.text(
        x, y, label,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight=fontweight,
        color=color,
        ha="left",
        va="bottom",
    )


def style_dark_image_ax(ax, facecolor="black"):
    """Prepare an axes for microscopy or dark image plates."""
    ax.set_facecolor(facecolor)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax
```

For dark image plates, keep the label inside the panel:
`add_panel_label(ax, "a", x=0.01, y=0.98, color="white")`.

## Plot Helpers

```python
def make_grouped_bar(ax, categories, series, labels,
                     ylabel="Value", colors=None, annotate=False,
                     bar_width=0.8, error_kw=None):
    """Grouped bars. `series` is one 1D array per group."""
    import numpy as np

    if len(series) != len(labels):
        raise ValueError("series and labels must have the same length")
    if not series:
        raise ValueError("series must not be empty")
    n_cats = len(categories)
    for vals in series:
        if len(vals) != n_cats:
            raise ValueError("each series must match len(categories)")

    colors = colors or DEFAULT_COLORS
    error_kw = error_kw or {"elinewidth": 1.0, "capthick": 1.0, "capsize": 3}
    n_groups = len(series)
    width = bar_width / n_groups
    x = np.arange(n_cats)
    containers = []

    for i, (vals, label, color) in enumerate(zip(series, labels, colors)):
        offset = (i - (n_groups - 1) / 2) * width
        bars = ax.bar(
            x + offset, vals, width=width, label=label,
            color=color, edgecolor="black", linewidth=0.5, error_kw=error_kw,
        )
        containers.append(bars)
        if annotate:
            for bar, val in zip(bars, vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.2f}",
                    ha="center", va="bottom", fontsize=max(6, plt.rcParams["font.size"] - 1),
                )

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel)
    return containers
```

```python
def make_trend(ax, x, y_series, labels, colors=None, ylabel=None, xlabel=None,
               show_shadow=False, shadow_alpha=0.15, lw=1.5, marker="o",
               markersize=3):
    """Multi-line trend plot. 2D arrays are treated as repeated runs."""
    import numpy as np

    if len(y_series) != len(labels):
        raise ValueError("y_series and labels must have the same length")
    colors = colors or DEFAULT_COLORS
    x = np.asarray(x)

    for y, label, color in zip(y_series, labels, colors):
        y = np.asarray(y)
        if y.ndim == 2:
            if y.shape[1] != len(x):
                raise ValueError("2D y_series arrays must have shape (runs, len(x))")
            mean, std = y.mean(0), y.std(0)
        elif y.ndim == 1:
            if len(y) != len(x):
                raise ValueError("1D y_series arrays must match len(x)")
            mean, std = y, None
        else:
            raise ValueError("y_series arrays must be 1D or 2D")
        ax.plot(x, mean, color=color, lw=lw, marker=marker,
                markersize=markersize, label=label)
        if show_shadow and std is not None:
            ax.fill_between(x, mean - std, mean + std, color=color, alpha=shadow_alpha)

    if ylabel:
        ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)
```

```python
def make_forest_plot(ax, labels, estimates, ci_low, ci_high, colors=None,
                     ref=0.0, xlabel=None, xlim=None, marker="o",
                     markersize=4, lw=1.2):
    """Minimal forest plot for clinical or statistical panels."""
    import numpy as np

    lengths = {len(labels), len(estimates), len(ci_low), len(ci_high)}
    if len(lengths) != 1:
        raise ValueError("labels, estimates, ci_low, and ci_high must match")

    y = np.arange(len(labels))[::-1]
    colors = colors or [PALETTE["red_strong"]] * len(labels)

    for yi, est, lo, hi, color in zip(y, estimates, ci_low, ci_high, colors):
        ax.plot([lo, hi], [yi, yi], color=color, lw=lw)
        ax.plot(est, yi, marker=marker, ms=markersize, color=color)
    ax.axvline(ref, color=PALETTE["neutral_mid"], linestyle="--", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    if xlabel:
        ax.set_xlabel(xlabel)
    if xlim is not None:
        ax.set_xlim(xlim)
```

Use pale `ax.axhspan(...)` bands behind contiguous label groups when a clinical
triptych needs grouped rows.

```python
def make_heatmap(ax, matrix, x_labels=None, y_labels=None, cmap="magma",
                 cbar_label=None, annotate=False, fmt="{:.2f}", fontsize=6):
    """2D heatmap with optional colorbar and contrast-aware cell labels."""
    import numpy as np
    import matplotlib as mpl

    matrix = np.asarray(matrix)
    if matrix.ndim != 2:
        raise ValueError("matrix must be 2D")
    if x_labels is not None and len(x_labels) != matrix.shape[1]:
        raise ValueError("len(x_labels) must match matrix.shape[1]")
    if y_labels is not None and len(y_labels) != matrix.shape[0]:
        raise ValueError("len(y_labels) must match matrix.shape[0]")

    im = ax.imshow(matrix, cmap=cmap, aspect="auto")
    if cbar_label:
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_label(cbar_label)
    if x_labels is not None:
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=30, ha="right")
    if y_labels is not None:
        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels)
    if annotate:
        norm = mpl.colors.Normalize(vmin=matrix.min(), vmax=matrix.max())
        cmap_obj = plt.get_cmap(cmap)
        for (i, j), val in np.ndenumerate(matrix):
            r, g, b, _ = cmap_obj(norm(val))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            color = "white" if lum < 0.5 else "black"
            ax.text(j, i, fmt.format(val), ha="center", va="center",
                    fontsize=fontsize, color=color)
    ax.set_frame_on(False)
    return im
```

## Export Helper

```python
def save_publication_figure(fig, out_path, formats=("svg", "pdf", "tiff"),
                            dpi=600, bbox_inches="tight", pad=0.05,
                            close=True):
    """Save SVG/PDF/TIFF outputs and return the written paths."""
    from pathlib import Path

    base = Path(out_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    if base.suffix:
        base = base.with_suffix("")

    saved = []
    for fmt in formats:
        fmt = fmt.lower().lstrip(".")
        if fmt not in {"svg", "pdf", "tiff", "tif", "png"}:
            raise ValueError(f"Unsupported figure format: {fmt}")
        path = base.with_suffix("." + fmt)
        fig.savefig(path, dpi=dpi, bbox_inches=bbox_inches, pad_inches=pad)
        saved.append(str(path))

    if close:
        plt.close(fig)
    return saved
```

For final projects, list these outputs in `manifest.json` so
`validate-figure` can check the export bundle.

## Local Validation Rules

- Grouped bars: `len(series) == len(labels)` and each series length equals `len(categories)`.
- Trends: every 1D line must match `len(x)`; 2D repeated-run arrays must be `(runs, len(x))`.
- Forest plots: `labels`, `estimates`, `ci_low`, and `ci_high` must have the same length.
- Heatmaps: `matrix` must be 2D; label lengths must match matrix dimensions.
- Final exports: include `.svg`; include `.pdf` and `.tiff` or `.png` for final QA.
- Keep one selected backend for plotting, previewing, exporting, and visual QA.
