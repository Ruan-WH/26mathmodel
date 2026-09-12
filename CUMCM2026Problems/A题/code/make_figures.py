# Academic Figure Skill Asset Confirmation (verified against assets/figures/)
# (a) LineTrend → assets/figures/LineTrend/plot_sweep.py → param inherit
# (b) LineTrend → assets/figures/LineTrend/plot_sweep.py → param inherit
# RULE: "native run" = load pre-rendered PNG via Image.open().ax.imshow().
#       "param inherit" = drawing function below that copies Class A/B/C values.
#       The production asset's data semantics differ, so only its clean line/marker structure is inherited.

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

# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update({
    "pdf.fonttype": 42,         # TrueType font embedding
    "svg.fonttype": "none",     # editable text in SVG
    "savefig.bbox": "tight",    # trim whitespace
    "savefig.dpi": 300,
})

def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)


import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
MM_TO_INCH = 1.0 / 25.4
TIME_COLORS = ["#BFD7EA", "#6BAED6", "#2166AC", "#762A83", "#B2182B"]


def require_fonts() -> None:
    font_manager.findfont("Times New Roman", fallback_to_default=False)
    for chinese_font in ("SimSun", "Songti SC", "STSong"):
        try:
            font_manager.findfont(chinese_font, fallback_to_default=False)
        except ValueError:
            continue
        mpl.rcParams["font.family"] = ["Times New Roman", chinese_font]
        return
    raise RuntimeError("需要 SimSun、Songti SC 或 STSong 中至少一种中文字体")


def load_summary(question: str) -> dict:
    return json.loads((RESULTS / question / "summary.json").read_text(encoding="utf-8"))


def nearest_indices(times: np.ndarray, requested: list[float]) -> list[int]:
    return [int(np.argmin(np.abs(times - value))) for value in requested]


def panel_labels(fig, axes: list[plt.Axes], labels: str = "ab") -> None:
    for label, axis in zip(labels, axes):
        box = axis.get_position()
        fig.text(
            0.5 * (box.x0 + box.x1),
            0.035,
            f"({label})",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
        )


def common_axis_style(axis: plt.Axes) -> None:
    axis.tick_params(length=3.0, width=0.6)
    axis.grid(False)


def plot_profiles(
    axis: plt.Axes,
    radius_cm: np.ndarray,
    values: np.ndarray,
    labels: list[str],
    ylabel: str,
    show_legend: bool = True,
) -> None:
    for index, (profile, label) in enumerate(zip(values, labels)):
        color = TIME_COLORS[index if len(values) == len(TIME_COLORS) else int(
            round(index * (len(TIME_COLORS) - 1) / max(len(values) - 1, 1))
        )]
        axis.plot(
            radius_cm,
            profile,
            color=color,
            linewidth=1.3,
            marker="o",
            markersize=2.3,
            markevery=4,
            label=label,
        )
    axis.set_xlabel("到药材中心的距离 / cm")
    axis.set_ylabel(ylabel)
    axis.set_xlim(float(radius_cm[0]), float(radius_cm[-1]))
    if show_legend:
        axis.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.01),
            ncol=min(len(labels), 3),
            columnspacing=0.9,
            handlelength=1.8,
        )
    common_axis_style(axis)


def figure_q1() -> None:
    data = np.load(RESULTS / "q1" / "fields.npz")
    times = data["times_s"]
    radius_cm = data["radius_m"] * 100.0
    requested = [100, 600, 1200, 1800]
    indexes = nearest_indices(times, requested)
    labels = [f"{time:d} s" for time in requested]
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM_TO_INCH, 68 * MM_TO_INCH),
        gridspec_kw={"wspace": 0.22},
    )
    plot_profiles(
        axes[0],
        radius_cm,
        data["temperature_c"][indexes],
        labels,
        "温度 / °C",
        show_legend=False,
    )
    plot_profiles(
        axes[1],
        radius_cm,
        data["moisture"][indexes],
        labels,
        "水分浓度 C / (kg/kg)",
        show_legend=False,
    )
    axes[1].set_ylim(1.4, 2.60)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.975),
        ncol=len(legend_labels),
        columnspacing=1.2,
        handlelength=1.8,
        handletextpad=0.45,
        borderaxespad=0.0,
    )
    fig.subplots_adjust(left=0.08, right=0.99, top=0.85, bottom=0.20, wspace=0.22)
    panel_labels(fig, list(axes))
    save_cns_figure(fig, str(FIGURES / "q1_preheat_profiles"))
    plt.close(fig)


def figure_q2() -> None:
    data = np.load(RESULTS / "q2" / "fields.npz")
    times = data["times_s"]
    radius_cm = data["radius_m"] * 100.0
    requested = [1800, 5400, 10800]
    indexes = nearest_indices(times, requested)
    labels = ["0.5 h", "1.5 h", "3.0 h"]
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM_TO_INCH, 72 * MM_TO_INCH),
        gridspec_kw={"wspace": 0.34},
    )
    plot_profiles(
        axes[0],
        radius_cm,
        data["temperature_c"][indexes],
        labels,
        "温度 / °C",
    )
    plot_profiles(
        axes[1],
        radius_cm,
        data["moisture"][indexes],
        labels,
        "水分浓度 / (kg·kg⁻¹)",
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.83, bottom=0.23, wspace=0.34)
    panel_labels(fig, list(axes))
    save_cns_figure(fig, str(FIGURES / "q2_coupled_profiles"))
    plt.close(fig)


def figure_q3() -> None:
    data = np.load(RESULTS / "q3" / "fields.npz")
    summary = load_summary("q3")
    time_h = data["times_s"] / 3600.0
    radius_cm = data["radius_m"] * 100.0
    end_h = float(summary["drying_time_h"])
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM_TO_INCH, 76 * MM_TO_INCH),
        gridspec_kw={"wspace": 0.36},
    )
    axes[0].plot(time_h, data["moisture"][:, 0], color=CATEGORICAL[0], linewidth=1.4, label="中心")
    axes[0].plot(
        time_h,
        data["moisture"][:, -1],
        color=CATEGORICAL[3],
        linewidth=1.2,
        linestyle="--",
        label="表面",
    )
    axes[0].axhline(0.15, color=ACCENT_RED, linewidth=0.8, linestyle=":", label="阈值 0.15")
    axes[0].axvline(end_h, color=GREY, linewidth=0.7, linestyle="--")
    axes[0].annotate(
        f"{end_h:.3f} h",
        xy=(end_h, 0.15),
        xytext=(end_h - 16, 0.42),
        arrowprops={"arrowstyle": "->", "lw": 0.7, "color": BLACK},
        fontsize=7,
    )
    axes[0].set_xlabel("时间 / h")
    axes[0].set_ylabel("水分浓度 / (kg·kg⁻¹)")
    axes[0].set_xlim(0, max(time_h))
    axes[0].set_ylim(0, 2.65)
    axes[0].legend(loc="upper right")
    common_axis_style(axes[0])

    requested_h = [6, 18, 36, 48, end_h]
    indexes = nearest_indices(time_h, requested_h)
    labels = ["6 h", "18 h", "36 h", "48 h", f"{end_h:.3f} h"]
    profiles = data["moisture"][indexes].copy()
    profiles[-1] = data["threshold_moisture"]
    plot_profiles(
        axes[1],
        radius_cm,
        profiles,
        labels,
        "水分浓度 / (kg·kg⁻¹)",
    )
    axes[1].axhline(0.15, color=ACCENT_RED, linewidth=0.8, linestyle=":")
    axes[1].set_ylim(0, 1.10)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.83, bottom=0.22, wspace=0.36)
    panel_labels(fig, list(axes))
    save_cns_figure(fig, str(FIGURES / "q3_threshold_diagnostics"))
    plt.close(fig)


def figure_q4() -> None:
    fixed = np.load(RESULTS / "q4" / "fixed_radius_counterfactual.npz")
    q4 = np.load(RESULTS / "q4" / "fields.npz")
    summary4 = load_summary("q4")
    time_fixed_h = fixed["times_s"] / 3600.0
    time4_h = q4["times_s"] / 3600.0
    end_fixed_h = float(
        summary4["fixed_radius_counterfactual"]["same_appendix4_properties_time_h"]
    )
    end4_h = float(summary4["drying_time_h"])
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(183 * MM_TO_INCH, 74 * MM_TO_INCH),
        gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.34},
    )
    axes[0].plot(
        time_fixed_h,
        fixed["moisture"][:, 0],
        color=CATEGORICAL[0],
        linewidth=1.3,
        linestyle="--",
        label="固定半径对照（附录 4 物性）",
    )
    axes[0].plot(
        time4_h,
        q4["moisture"][:, 0],
        color=ACCENT_RED,
        linewidth=1.5,
        label="收缩模型（问题 4）",
    )
    axes[0].axhline(0.15, color=GREY, linewidth=0.8, linestyle=":")
    axes[0].scatter(
        [end_fixed_h, end4_h],
        [0.15, 0.15],
        color=[CATEGORICAL[0], ACCENT_RED],
        s=18,
        zorder=4,
    )
    axes[0].annotate(
        f"{end4_h:.3f} h",
        xy=(end4_h, 0.15),
        xytext=(end4_h - 15, 0.43),
        arrowprops={"arrowstyle": "->", "lw": 0.7, "color": ACCENT_RED},
        color=ACCENT_RED,
        fontsize=7,
    )
    axes[0].set_xlabel("时间 / h")
    axes[0].set_ylabel("中心水分浓度 / (kg·kg⁻¹)")
    axes[0].set_xlim(0, max(time_fixed_h))
    axes[0].set_ylim(0, 2.65)
    axes[0].legend(loc="upper right")
    common_axis_style(axes[0])

    axes[1].plot(
        time4_h,
        q4["radii_m"] * 100.0,
        color=CATEGORICAL[4],
        linewidth=1.4,
        marker="o",
        markersize=2.2,
        markevery=max(1, len(time4_h) // 12),
    )
    axes[1].scatter([end4_h], [summary4["radius_at_end_cm"]], color=ACCENT_RED, s=18, zorder=4)
    axes[1].annotate(
        f"{summary4['radius_at_end_cm']:.3f} cm",
        xy=(end4_h, summary4["radius_at_end_cm"]),
        xytext=(end4_h - 17, 1.33),
        arrowprops={"arrowstyle": "->", "lw": 0.7, "color": BLACK},
        fontsize=7,
    )
    axes[1].set_xlabel("时间 / h")
    axes[1].set_ylabel("药材半径 / cm")
    axes[1].set_xlim(0, max(time4_h))
    axes[1].set_ylim(1.12, 2.05)
    common_axis_style(axes[1])
    fig.subplots_adjust(left=0.09, right=0.98, top=0.84, bottom=0.23, wspace=0.34)
    panel_labels(fig, list(axes))
    save_cns_figure(fig, str(FIGURES / "q4_shrinkage_comparison"))
    plt.close(fig)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    require_fonts()
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure_q1()
    figure_q2()
    figure_q3()
    figure_q4()
    print("Generated q1--q4 PDF and PNG figures.")


if __name__ == "__main__":
    main()
