# Typography & Font Specifications

> **BASELINE — COPY VERBATIM:** The code block below must be copied into every generated script BEFORE any plotting code. It is the first thing that executes. Do not modify, do not omit lines, do not "write something similar".

```python
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
```

```r
# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
library(ggplot2)
theme_cns <- theme_bw(base_size = 8, base_family = "Arial") +
  theme(
    axis.title = element_text(size = 8),
    axis.text = element_text(size = 7, color = "#333333"),
    legend.title = element_text(size = 8, face = "bold"),
    legend.text = element_text(size = 7),
    strip.text = element_text(size = 8, face = "bold"),
    panel.grid = element_blank(),
    legend.background = element_blank(),
    legend.key = element_blank()
  )
```

---

## Font Family

General CNS figures default to sans-serif: **Preferred:** Arial, Helvetica. **Fallback:** Liberation Sans.

### CUMCM bilingual override

When this skill is invoked through `3coding-visual`, apply the following block immediately after the mandatory baseline. It preserves Times New Roman for English letters, Arabic numerals, and mathematics while falling back to SimSun only for Chinese glyphs. Do not put SimSun first: doing so also renders Latin text in SimSun.

```python
mpl.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold",
    "mathtext.sf": "Times New Roman",
})
```

Before export, verify that both `Times New Roman` and `SimSun` are installed. After PDF export, use `pdffonts` or an equivalent inspector to confirm that both fonts are embedded.

## Font Size Floor

No text element below 5 pt at final print dimensions. Axis ticks: 5-6 pt. Labels: 6-7 pt. Panel labels: 8-9 pt bold.

## R ggplot2 Setup

```r
library(ggplot2)

theme_cns <- theme_bw(base_size = 7, base_family = "Arial") +
  theme(
    axis.title = element_text(size = 8),
    axis.text = element_text(size = 6),
    legend.title = element_text(size = 7, face = "bold"),
    legend.text = element_text(size = 6),
    strip.text = element_text(size = 8, face = "bold")
  )
```

## R ComplexHeatmap Setup

```r
library(ComplexHeatmap)
library(grid)

ht_opt(
  heatmap_column_names_gp = gpar(fontfamily = "Arial", fontsize = 6),
  heatmap_row_names_gp = gpar(fontfamily = "Arial", fontsize = 6),
  legend_title_gp = gpar(fontfamily = "Arial", fontsize = 7, fontface = "bold"),
  legend_labels_gp = gpar(fontfamily = "Arial", fontsize = 6)
)
```

## Cross-platform Font Notes

- Windows: Arial is installed by default
- macOS: Helvetica is installed by default; Arial is also available
- Linux: Neither Arial nor Helvetica is guaranteed. Use `Liberation Sans` or install `fonts-liberation` / `msttcorefonts`
- For R on Linux: use `showtext` package to register and embed fonts; export with `cairo_pdf()` device
- Always embed fonts in PDF output: `pdf.fonttype: 42` (matplotlib), `cairo_pdf()` (R)
