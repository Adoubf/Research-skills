# Tutorials - Nature Figure Making

Use this file when the user needs an end-to-end Python example after selecting
Python as the backend. These examples assume the helpers from `api.md` have been
copied into the final plotting script.

Each final tutorial should still use user-provided source data. The arrays below
are placeholders for structure only.

## Shared Setup

```python
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Copy PALETTE, apply_publication_style, and save_publication_figure from api.md.
apply_publication_style(font_size=8, axes_linewidth=1.0)
```

## Tutorial 1: Multi-Metric Method Comparison

Use when several methods are compared across multiple metrics and one shared legend
is enough.

```python
methods = ["Baseline A", "Baseline B", "Ours small", "Ours large"]
metrics = ["Metric 1", "Metric 2", "Metric 3"]
colors = [
    PALETTE_NMI_PASTEL["baseline_dark"],
    PALETTE_NMI_PASTEL["baseline_mid"],
    PALETTE_NMI_PASTEL["ours_tiny"],
    PALETTE_NMI_PASTEL["ours_large"],
]
mean = {
    "Metric 1": np.array([0.81, 0.83, 0.89, 0.92]),
    "Metric 2": np.array([0.63, 0.67, 0.74, 0.79]),
    "Metric 3": np.array([0.41, 0.45, 0.53, 0.58]),
}
err = {name: values * 0.03 for name, values in mean.items()}

fig = plt.figure(figsize=(7.2, 2.4))
gs = fig.add_gridspec(1, len(metrics) + 1, width_ratios=[1, 1, 1, 0.75])

handles, labels = None, None
for i, metric in enumerate(metrics):
    ax = fig.add_subplot(gs[0, i])
    ax.bar(
        np.arange(len(methods)),
        mean[metric],
        yerr=err[metric],
        capsize=2,
        color=colors,
        label=methods,
        error_kw={"elinewidth": 0.8, "capthick": 0.8},
    )
    if i == 0:
        handles, labels = ax.get_legend_handles_labels()
    values = mean[metric]
    margin = max((values.max() - values.min()) * 0.15, 1e-9)
    ax.set_ylim(values.min() - margin, values.max() + margin)
    ax.set_ylabel(metric)
    ax.set_xticks([])

ax_leg = fig.add_subplot(gs[0, -1])
ax_leg.legend(handles, labels, loc="center", frameon=False)
ax_leg.set_axis_off()

save_publication_figure(fig, "figures/method_comparison")
```

Record in `manifest.json`: source CSV, script path, SVG/PDF/TIFF outputs, and QA checks.

## Tutorial 2: Ablation Bar Chart

Use when the same method is progressively assembled or ablated.

```python
configs = ["Minimal", "+ Module A", "+ Module B", "Full"]
values = np.array([0.72, 0.78, 0.84, 0.88])
errors = np.array([0.02, 0.02, 0.01, 0.01])

base = (0.215686, 0.458824, 0.729412)
alphas = np.linspace(0.25, 1.0, len(configs))
colors = [(base[0], base[1], base[2], alpha) for alpha in alphas]

fig, ax = plt.subplots(figsize=(3.4, 2.4))
ax.barh(np.arange(len(configs)), values, xerr=errors, color=colors,
        ecolor="black", capsize=2)
ax.set_yticks(np.arange(len(configs)))
ax.set_yticklabels(configs)
span = values.max() - values.min()
ax.set_xlim(values.min() - span * 0.2, values.max() + span * 0.12)
ax.set_xlabel("Score")

save_publication_figure(fig, "figures/ablation")
```

Use one hue with alpha variation; do not assign unrelated colors to ablation stages.

## Tutorial 3: Multi-Panel Trend with Shared Legend

Use when two or more trend panels share the same line identities.

```python
methods = ["Baseline", "Ours small", "Ours large"]
colors = [
    PALETTE_NMI_PASTEL["baseline_mid"],
    PALETTE_NMI_PASTEL["ours_tiny"],
    PALETTE_NMI_PASTEL["ours_large"],
]
x = np.arange(0, 100, 10)
rng = np.random.default_rng(0)

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), width_ratios=[1, 1, 0.7])

for ax, panel_name in zip(axes[:2], ["Training", "Validation"]):
    for method, color in zip(methods, colors):
        y = 0.50 + 0.35 * (1 - np.exp(-x / 30)) + rng.normal(0, 0.01, len(x))
        if "Ours small" in method:
            y += 0.02
        elif "Ours large" in method:
            y += 0.04
        ax.plot(x, y, color=color, lw=1.2, marker="o", markersize=2.5, label=method)
    ax.set_title(panel_name)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")

handles, labels = axes[0].get_legend_handles_labels()
axes[2].legend(handles, labels, loc="center", frameon=False)
axes[2].set_axis_off()

save_publication_figure(fig, "figures/trends")
```

If event annotations are needed, use the sparse event pattern in `common-patterns.md`.

## Tutorial 4: Signed Heatmap

Use when columns have different directional meanings, such as score-up and error-down.

```python
methods = ["Method A", "Method B", "Method C", "Method D"]
metrics = ["Score (+)", "Error (-)", "F1 (+)", "Loss (-)"]
matrix = np.array([
    [0.88, 0.12, 0.85, 0.20],
    [0.81, 0.18, 0.78, 0.28],
    [0.75, 0.25, 0.72, 0.35],
    [0.70, 0.30, 0.68, 0.40],
])

fig, ax = plt.subplots(figsize=(3.6, 2.6))
n_rows, n_cols = matrix.shape

for j in range(n_cols):
    higher_is_better = "(+)" in metrics[j]
    cmap = plt.cm.Reds if higher_is_better else plt.cm.Blues_r
    norm = plt.Normalize(vmin=matrix[:, j].min(), vmax=matrix[:, j].max())
    ax.imshow(matrix[:, j:j + 1], cmap=cmap, norm=norm, aspect="auto",
              extent=[j - 0.5, j + 0.5, 0, n_rows], origin="lower")

for (i, j), value in np.ndenumerate(matrix):
    ax.text(j, i + 0.5, f"{value:.2f}", ha="center", va="center", fontsize=6)

ax.set_xlim(-0.5, n_cols - 0.5)
ax.set_xticks(np.arange(n_cols))
ax.set_xticklabels(metrics, rotation=30, ha="right")
ax.set_yticks(np.arange(n_rows) + 0.5)
ax.set_yticklabels(methods)
ax.set_frame_on(False)
ax.invert_yaxis()

save_publication_figure(fig, "figures/signed_heatmap")
```

For rich biological annotations, consider R/ComplexHeatmap instead of forcing this
Matplotlib pattern.

## Related Files

- [api.md](api.md) - helper constants and function contracts
- [common-patterns.md](common-patterns.md) - layout and encoding choices
- [design-theory.md](design-theory.md) - typography, color, and composition rationale
- [chart-types.md](chart-types.md) - specialized chart snippets
