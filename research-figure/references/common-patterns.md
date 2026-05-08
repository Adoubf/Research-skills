# Common Patterns - Nature Figure Making

Use this file after the figure contract is set and Python has been selected.
It is a pattern index, not a full tutorial. For helper implementations, use
`api.md`. For rationale, use `design-theory.md`.

## Pattern Selection

| Need | Pattern |
|---|---|
| 3-4 metrics across many methods | Ultra-wide multi-metric bars |
| Data panels need a large legend | Dedicated legend axis |
| Method names already appear in legend | Hide categorical x ticks |
| Values occupy a narrow numerical band | Tighten y-axis to data range |
| Ablation variants of one method | Alpha-graduated single hue |
| Print-safe bars or areas | Add hatch encoding |
| Same methods across panels | Semantic color mapping |
| Dense repeated categorical regions | Direct labels inside regions |
| Mechanism or workflow leads the figure | Schematic hero + quant row |
| Microscopy or fluorescence plates | Dark image plate grid |
| Clinical longitudinal/effect/summary figure | Clinical triptych |
| One panel carries the central evidence | Asymmetric hero layout |

## Layout Patterns

### Ultra-wide multi-metric bars

Use when several metrics compare the same methods and labels would crowd at
journal width.

```python
fig = plt.figure(figsize=(28, 6))
gs = fig.add_gridspec(1, len(metrics) + 1, width_ratios=[1] * len(metrics) + [0.55])

for i, metric in enumerate(metrics):
    ax = fig.add_subplot(gs[0, i])
    bars = ax.bar(x, values[metric], color=colors, label=methods)
    ax.set_ylabel(metric)
    ax.set_xticks([])

ax_leg = fig.add_subplot(gs[0, -1])
ax_leg.legend(*axes[0].get_legend_handles_labels(), loc="center", frameon=False)
ax_leg.set_axis_off()
```

Keep the figure wide enough for left-to-right scanning. For final manuscript pages,
convert slide-scale font sizes back to the target final-size range.

### Dedicated legend axis

Use when a legend would cover data or repeat across panels.

```python
handles, labels = ax_main.get_legend_handles_labels()
ax_legend.legend(handles, labels, loc="center", frameon=False)
ax_legend.set_axis_off()
```

Prefer one shared legend strip or side axis over repeated legends.

### Schematic hero + quant row

Use when a mechanism, device, workflow, or fabrication story must be understood
before the quantitative evidence.

```python
fig = plt.figure(figsize=(7.2, 6.2))
gs = fig.add_gridspec(2, 4, height_ratios=[2.2, 1.0], hspace=0.18, wspace=0.28)

ax_a = fig.add_subplot(gs[0, :])    # hero schematic
ax_b = fig.add_subplot(gs[1, 0])
ax_c = fig.add_subplot(gs[1, 1:3])
ax_d = fig.add_subplot(gs[1, 3])
```

Give the hero schematic about 45-60% of the figure height. Reuse its palette in
the lower plots, but keep supporting panels visually quieter.

### Dark image plate grid

Use for microscopy, histology, volume rendering, or fluorescence-heavy panels.

```python
fig = plt.figure(figsize=(7.2, 6.5))
gs = fig.add_gridspec(n_rows, n_cols, hspace=0.08, wspace=0.04)

for r in range(n_rows):
    for c in range(n_cols):
        ax = fig.add_subplot(gs[r, c])
        style_dark_image_ax(ax)
```

Use black only inside image cells. Put channel labels, scale bars, crop guides,
and row labels directly on the plate. Keep crop geometry and scale-bar placement
consistent across cells.

### Clinical triptych

Use for outcome-over-time figures that combine trajectories, effect sizes, and
summary proportions.

```python
fig = plt.figure(figsize=(7.2, 6.8))
gs = fig.add_gridspec(3, 3, height_ratios=[1.0, 1.35, 0.8], hspace=0.28, wspace=0.32)

axes_top = [fig.add_subplot(gs[0, i]) for i in range(3)]
axes_mid = [fig.add_subplot(gs[1, i]) for i in range(3)]
axes_bot = [fig.add_subplot(gs[2, i]) for i in range(3)]
```

Keep columns semantically parallel. Put the shared legend above the top row.
Use dashed vertical reference lines and pale group bands in forest-plot rows.

### Asymmetric hero layout

Use when one panel carries the central evidence and should span rows or columns.

```python
fig = plt.figure(figsize=(7.2, 5.8))
gs = fig.add_gridspec(3, 4, hspace=0.25, wspace=0.28)

ax_a = fig.add_subplot(gs[0, :2])
ax_b = fig.add_subplot(gs[0, 2])
ax_c = fig.add_subplot(gs[1, :2])
ax_d = fig.add_subplot(gs[1, 2])
ax_e = fig.add_subplot(gs[:, 3])  # hero panel
ax_f = fig.add_subplot(gs[2, :2])
```

Do not force equal subplot sizes when evidence value is unequal.

## Encoding Patterns

### Hide categorical x ticks

Use when methods are named in a legend, direct labels, or panel title.

```python
ax.set_xticks([])
```

Do not remove x ticks when category order itself is a key result.

### Tighten numerical axes

Use when all values occupy a narrow range.

```python
span = values.max() - values.min()
margin = max(span * 0.12, 1e-9)
ax.set_ylim(values.min() - margin, values.max() + margin)
```

Avoid 0-100 axes for metrics that all sit around 80-95 unless zero is scientifically
meaningful.

### Alpha-graduated ablation bars

Use for progressive variants of the same method.

```python
base = (0.215686, 0.458824, 0.729412)  # #3775BA
alphas = np.linspace(0.25, 1.0, len(configs))
colors = [(base[0], base[1], base[2], a) for a in alphas]
```

Use full opacity for the complete method and lower opacity for more ablated variants.

### Hatch encoding

Use when neighboring fills may collapse in grayscale or print.

```python
hatches = ["/", "\\", ".", "x", "o", "+"]
for container, hatch in zip(bar_containers, hatches):
    for patch in container:
        patch.set_hatch(hatch)
        patch.set_edgecolor("black")
        patch.set_linewidth(0.5)
```

### Semantic color mapping

Use one stable mapping for the whole figure.

```python
method_colors = {
    "Baseline A": PALETTE_NMI_PASTEL["baseline_dark"],
    "Baseline B": PALETTE_NMI_PASTEL["baseline_mid"],
    "Ours small": PALETTE_NMI_PASTEL["ours_tiny"],
    "Ours large": PALETTE_NMI_PASTEL["ours_large"],
}
colors = [method_colors[name] for name in methods]
```

Reserve green/red mainly for signed deltas, thresholds, warnings, or biological
direction, not arbitrary series identity.

### Direct labels inside regions

Use when repeated categorical regions would require a large legend.

```python
for x_text, y_text, label, color in label_specs:
    ax.text(x_text, y_text, label, color=color, ha="center", va="center", fontsize=7)
```

Place direct labels only in stable, visually large regions. Add a subtle white or
black stroke only when the fill underneath changes strongly.

### Event annotations on trends

Use when a time series has sparse, interpretable events.

```python
x_index = {label: i for i, label in enumerate(x_labels)}
for event_x, event_label in events.items():
    if event_x not in x_index:
        continue
    i = x_index[event_x]
    ax.annotate(
        event_label,
        xy=(i, y_values[i]),
        xytext=(i, y_values[i] + dy),
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": "black"},
    )
```

Keep event labels sparse. If many events compete with the trend, move them to a
separate timeline panel.

## Related Files

- [api.md](api.md) - Python helper constants and function contracts
- [design-theory.md](design-theory.md) - typography, color, layout rationale
- [nature-2026-observations.md](nature-2026-observations.md) - Nature-family archetypes
- [tutorials.md](tutorials.md) - end-to-end examples
- [chart-types.md](chart-types.md) - specialized chart snippets
