# Specialized Chart Types

Use this file for chart families not covered by the standard helpers in `api.md`
or the layout patterns in `common-patterns.md`.

## Selection Guide

| Need | Use |
|---|---|
| Many methods across many benchmarks with heterogeneous scales | Radar / polar chart |
| Conceptual geometry, embedding space, or mechanism illustration | Shaded sphere or 3D scatter |
| Cumulative composition over ordered categories/time | Filled area or stacked area |
| Values span orders of magnitude | Log-scale bar chart |
| Positive and negative values share one axis | Custom spine at zero |

## Radar / Polar Chart

Use radar plots only when the spokes are meaningful and numerous benchmark panels
would be harder to compare. Normalize each spoke independently and document the
normalization range.

```python
def plot_radar(ax, methods, colors, spoke_labels, value_matrix,
               spoke_ranges, display_range=(45, 90)):
    """value_matrix shape: (n_spokes, n_methods)."""
    import numpy as np

    r_lo, r_hi = display_range
    n_spokes, n_methods = value_matrix.shape
    if n_spokes != len(spoke_labels):
        raise ValueError("spoke_labels must match value_matrix rows")
    if n_methods != len(methods):
        raise ValueError("methods must match value_matrix columns")

    angles = np.linspace(2 * np.pi, 0, n_spokes, endpoint=False)
    closed_angles = np.append(angles, angles[0])

    def normalize(value, label):
        lo, hi = spoke_ranges.get(label, (0, 100))
        if hi <= lo:
            return (r_lo + r_hi) / 2
        frac = np.clip((value - lo) / (hi - lo), 0, 1)
        return r_lo + (r_hi - r_lo) * frac

    for j, (method, color) in enumerate(zip(methods, colors)):
        vals = np.array([normalize(value_matrix[i, j], spoke_labels[i])
                         for i in range(n_spokes)])
        closed_vals = np.append(vals, vals[0])
        ax.plot(closed_angles, closed_vals, color=color, lw=1.2, label=method)
        ax.fill(closed_angles, closed_vals, color=color, alpha=0.05)
        ax.scatter(angles, vals, color=color, s=10, zorder=5)

    ax.set_ylim(r_lo, r_hi)
    ax.set_theta_zero_location("N")
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for angle in angles:
        ax.plot([angle, angle], [r_lo, r_hi], color="#A8A8A8", lw=0.4)
    ax.plot(closed_angles, np.full_like(closed_angles, r_hi), color="black", lw=0.6)
    ax.set_xticks(angles)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    for angle, label in zip(angles, spoke_labels):
        ax.text(angle, r_hi + 6, label, ha="center", va="center", fontsize=6)
```

Key settings:

- Start at the top with `set_theta_zero_location("N")`.
- Remove default grid/spines and draw custom spokes.
- Put the legend outside the polar data region.
- Do not use a radar plot for fewer than about five spokes unless the circular metaphor is scientifically meaningful.

## 3D / Conceptual Illustration

Use for geometric conceptual diagrams, not for precise quantitative comparison.
If the plot must support a quantitative claim, pair it with a 2D quantification panel.

```python
def draw_shaded_sphere(ax, light_dir=(-0.5, 0.5, 0.8), resolution=384,
                       alpha=1.0, extent=(-1, 1, -1, 1)):
    """Draw a 2D shaded disk that reads as a sphere."""
    import numpy as np

    xs = np.linspace(extent[0], extent[1], resolution)
    ys = np.linspace(extent[2], extent[3], resolution)
    x, y = np.meshgrid(xs, ys)
    r2 = x ** 2 + y ** 2
    mask = r2 <= 1.0

    z = np.zeros_like(x)
    z[mask] = np.sqrt(1.0 - r2[mask])
    normals = np.stack([x, y, z], axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True) + 1e-9

    light = np.array(light_dir, dtype=float)
    light /= np.linalg.norm(light)
    intensity = np.maximum(0, normals @ light)

    image = np.ones_like(x)
    image[mask] = np.clip(0.2 + 0.9 * intensity[mask], 0, 1)
    ax.imshow(image, cmap="gray", extent=list(extent), vmin=0, vmax=1, alpha=alpha)
    ax.set_axis_off()
```

```python
def plot_3d_arrows(ax, points, vectors, point_color="#0F4D92",
                   arrow_color="#B64342"):
    """3D scatter with vector arrows for conceptual directionality."""
    from matplotlib.patches import FancyArrowPatch
    from mpl_toolkits.mplot3d import proj3d
    import numpy as np

    class Arrow3D(FancyArrowPatch):
        def __init__(self, xs, ys, zs, *args, **kwargs):
            super().__init__((0, 0), (0, 0), *args, **kwargs)
            self._verts3d = xs, ys, zs

        def do_3d_projection(self, renderer=None):
            xs, ys, zs = proj3d.proj_transform(*self._verts3d, self.axes.get_proj())
            self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
            return np.min(zs)

    ax.scatter(points[:, 0], points[:, 1], points[:, 2],
               s=30, color=point_color, alpha=0.55)
    for point, vec in zip(points, vectors):
        arrow = Arrow3D(
            [point[0], point[0] + vec[0]],
            [point[1], point[1] + vec[1]],
            [point[2], point[2] + vec[2]],
            mutation_scale=10, lw=1.5, arrowstyle="->",
            color=arrow_color, alpha=0.8,
        )
        ax.add_artist(arrow)
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
```

## Filled or Stacked Area

Use for cumulative composition or ordered contributions. Add hatches when adjacent
fills have similar luminance or print safety matters.

```python
ax.fill_between(x, 0, y_bottom, color="#F6CFCB", label="Category A")
ax.fill_between(x, y_bottom, y_top, color="#9BC8FA",
                hatch="///", edgecolor="black", linewidth=0.3,
                label="Category B")
ax.plot(x, y_top, lw=1.2, color="#0F4D92")
```

If exact values matter, overlay a boundary line. If category labels are stable and
large enough, use direct labels inside the filled regions instead of a large legend.

## Log-Scale Bars

Use when values span orders of magnitude. Annotate in multiplicative space.

```python
ax.set_yscale("log")
ax.bar(x, values, color=colors)
for i, value in enumerate(values):
    ax.text(i, value * 1.15, f"{value:.2g}", ha="center", va="bottom", fontsize=6)
```

Do not use log scale for values that can be zero or negative unless the transform
and excluded values are explicitly documented.

## Custom Zero Spine

Use for signed bars or effects where the zero line is the comparison reference.

```python
ax.spines["bottom"].set_position(("data", 0))
ax.xaxis.set_ticks_position("bottom")
ax.axhline(0, color="#767676", lw=0.8)
```

Keep positive and negative encodings symmetric unless the scientific scale is asymmetric.

## Related Files

- [api.md](api.md) - Python helper constants and function contracts
- [common-patterns.md](common-patterns.md) - standard layout and encoding patterns
- [design-theory.md](design-theory.md) - design decision rationale
- [tutorials.md](tutorials.md) - end-to-end Python examples
