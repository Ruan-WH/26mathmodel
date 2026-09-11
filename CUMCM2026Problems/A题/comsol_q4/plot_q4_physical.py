# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 8,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})

mpl.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold",
    "mathtext.sf": "Times New Roman",
})

# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update({
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
})

def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)


from pathlib import Path
import json

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D


# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
    "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999",
]
DIVERGING   = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL  = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED  = "#B2182B"
GREY        = "#999999"
BLACK       = "#222222"


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "results" / "q4" / "fields.npz"
from analyze_q4_comsol import baseline_profile, comparison_times
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

# Asset confirmation: assets/figures was checked; no cylindrical physical-field asset exists.
# Cross-type inheritance: use the Q4 COMSOL field arrays and measured radius history directly.


def nearest(a, value):
    return int(np.argmin(np.abs(a - value)))


def interp_profile(xi_source, values, xi_target):
    return np.interp(xi_target, xi_source, values)


def draw_cylinder(ax, radius_cm, length_cm, xi, moisture, norm, cmap, title, initial_radius=2.0):
    # Side surface carries the local surface value; front face exposes the radial solution.
    theta = np.linspace(0, 2*np.pi, 120)
    z = np.linspace(0, length_cm, 55)
    th, zz = np.meshgrid(theta, z)
    xx = radius_cm * np.cos(th)
    yy = radius_cm * np.sin(th)
    side_color = cmap(norm(np.full_like(xx, moisture[-1])))
    ax.plot_surface(zz, xx, yy, facecolors=side_color, shade=True,
                    linewidth=0, antialiased=True, alpha=0.72)

    rr = np.linspace(0, radius_cm, 90)
    th2, rr2 = np.meshgrid(theta, rr)
    xf = rr2 * np.cos(th2)
    yf = rr2 * np.sin(th2)
    cf = interp_profile(xi, moisture, np.clip(rr2 / radius_cm, 0, 1))
    ax.plot_surface(np.zeros_like(xf), xf, yf, facecolors=cmap(norm(cf)),
                    shade=False, linewidth=0, antialiased=True)

    # Initial outline makes the magnitude of shrinkage readable in every panel.
    ax.plot(np.zeros_like(theta), initial_radius*np.cos(theta), initial_radius*np.sin(theta),
            color=GREY, ls=(0, (2, 2)), lw=0.8, alpha=0.8)
    ax.plot([0, length_cm], [0, 0], [0, 0], color=BLACK, lw=0.45, alpha=0.6)
    ax.set_title(title, pad=1.5)
    ax.set_xlim(-0.4, length_cm + 0.4)
    ax.set_ylim(-2.15, 2.15)
    ax.set_zlim(-2.15, 2.15)
    ax.set_box_aspect((length_cm + 0.8, 4.3, 4.3))
    ax.view_init(elev=20, azim=-63)
    ax.set_axis_off()


def make_physical_plate(comsol):
    times = comsol["times_s"]
    xi = comsol["x_ref_m"] / 0.02
    moisture = comsol["moisture"]
    radii = comsol["radii_m"] * 100
    chosen = [0.0, 21600.0, 86400.0, 182956.80447014328]
    titles = ["0 h", "6 h", "24 h", "50.82 h (终点)"]
    cmap = LinearSegmentedColormap.from_list("moisture_blue", SEQUENTIAL, N=256)
    norm = LogNorm(vmin=0.05, vmax=2.55)

    mm = 1 / 25.4
    fig = plt.figure(figsize=(183*mm, 58*mm))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 1, 1, 0.055], wspace=0.03)
    for k, (target, title) in enumerate(zip(chosen, titles)):
        i = nearest(times, target)
        ax = fig.add_subplot(gs[0, k], projection="3d")
        draw_cylinder(ax, float(radii[i]), 6.0, xi, moisture[i], norm, cmap,
                      f"{title}\n$R={radii[i]:.3f}$ cm")
        ax.text2D(0.01, 0.95, chr(ord('a') + k), transform=ax.transAxes,
                  fontsize=9, fontweight="bold", color=BLACK)
    cax = fig.add_subplot(gs[0, 4])
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("Moisture content, $C$ (kg kg$^{-1}$)")
    cb.set_ticks([0.05, 0.1, 0.2, 0.5, 1, 2.55])
    cb.set_ticklabels(["0.05", "0.10", "0.20", "0.50", "1.0", "2.55"])
    cb.outline.set_linewidth(0.5)
    fig.suptitle("第四问：收缩圆柱药材内部水分场（COMSOL 轴对称解重构）", y=0.995)
    save_cns_figure(fig, OUT / "q4_comsol_physical_moisture_field")
    plt.close(fig)


def make_validation_figure(comsol, baseline):
    ct = comsol["times_s"]
    cxi = comsol["x_ref_m"] / 0.02
    cm = comsol["moisture"]
    cr = comsol["radii_m"] * 100
    bxi = baseline["xi"]
    event_time = json.loads(BASE.with_name("summary.json").read_text(encoding="utf-8"))["drying_time_s"]
    chosen = [21600.0, 86400.0, event_time]
    labels = ["6 h", "24 h", "50.82 h"]
    colors = [CATEGORICAL[0], CATEGORICAL[3], CATEGORICAL[1]]

    mm = 1 / 25.4
    fig, axes = plt.subplots(1, 3, figsize=(183*mm, 66*mm), gridspec_kw={"wspace": 0.38})
    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.25, top=0.84)
    ax = axes[0]
    for target, label, color in zip(chosen, labels, colors):
        ic = nearest(ct, target)
        r_cm = cxi * cr[ic]
        base_at_cxi = interp_profile(bxi, baseline_profile(baseline, "moisture", target, event_time), cxi)
        ax.plot(r_cm, cm[ic], color=color, lw=1.5, label=label)
        pick = np.unique(np.r_[np.arange(0, len(cxi), 10), len(cxi)-1-np.array([1, 2, 5])])
        ax.plot(r_cm[pick], base_at_cxi[pick], "o", ms=2.8, mfc="white",
                mec=color, mew=0.7)
    ax.set_xlabel("Physical radius, $r$ (cm)")
    ax.set_ylabel("Moisture content, $C$ (kg kg$^{-1}$)")
    ax.set_xlim(0, 1.45)
    ax.legend(title="干燥时间", loc="upper right", bbox_to_anchor=(1.17, 1.02))
    ax.text(0.5, -0.30, "（a）径向水分剖面", transform=ax.transAxes,
            ha="center", va="top", fontsize=8)

    ax = axes[1]
    # Match the six times reported in the numerical comparison and paper.
    parity_x, parity_y = [], []
    for target in comparison_times(event_time):
        ic = nearest(ct, target)
        if abs(ct[ic] - target) > 1e-6:
            raise ValueError("Regenerate q4_comsol_fields.npz with exact study output times")
        parity_x.extend(interp_profile(bxi, baseline_profile(baseline, "moisture", target, event_time), cxi))
        parity_y.extend(cm[ic])
    parity_x, parity_y = np.asarray(parity_x), np.asarray(parity_y)
    lo, hi = 0.045, 1.82
    ax.plot([lo, hi], [lo, hi], color=GREY, ls="--", lw=0.7)
    ax.scatter(parity_x, parity_y, s=8, color=CATEGORICAL[0], alpha=0.7,
               edgecolors="none", rasterized=True)
    ax.set_xlabel("Reference moisture content")
    ax.set_ylabel("COMSOL moisture content")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    err = np.max(np.abs(parity_y - parity_x))
    ax.text(0.05, 0.92, f"$\\max|\\Delta C|={err:.5f}$", transform=ax.transAxes)
    ax.text(0.5, -0.30, "（b）COMSOL 与基准模型逐点校核", transform=ax.transAxes,
            ha="center", va="top", fontsize=8)

    ax = axes[2]
    ax.plot(ct/3600, cr, color=CATEGORICAL[0], lw=1.5)
    ax.fill_between(ct/3600, cr, 2.02, color=CATEGORICAL[0], alpha=0.10)
    event_h = event_time/3600
    ax.axvline(event_h, color=ACCENT_RED, ls=(0, (3, 2)), lw=1.0)
    ax.scatter([event_h], [1.2], color=ACCENT_RED, s=18, zorder=3)
    ax.annotate("主模型达标时刻\n50.82 h", (event_h, 1.2), xytext=(-38, 18),
                textcoords="offset points", arrowprops=dict(arrowstyle="-", lw=0.6),
                ha="center", fontsize=7)
    ax.set_xlabel("Time, $t$ (h)")
    ax.set_ylabel("Herb radius, $R(t)$ (cm)")
    ax.set_xlim(0, 52)
    ax.set_ylim(1.15, 2.05)
    ax.text(0.5, -0.30, "（c）药材半径收缩历程", transform=ax.transAxes,
            ha="center", va="top", fontsize=8)

    fig.suptitle("COMSOL 物理场剖面、独立数值校核与收缩历程", y=0.96)
    save_cns_figure(fig, OUT / "q4_comsol_profiles_validation")
    plt.close(fig)
    return {"max_abs_moisture_difference": float(err), "comparison_points": len(parity_x),
            "baseline_saved_nodes": len(bxi)}


def main():
    comsol = np.load(HERE / "q4_comsol_fields.npz")
    with np.load(BASE) as archive:
        baseline = {key: archive[key] for key in archive.files}
    make_physical_plate(comsol)
    make_validation_figure(comsol, baseline)
    print(json.dumps({"output": str(OUT), "figures": sorted(p.name for p in OUT.iterdir())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
