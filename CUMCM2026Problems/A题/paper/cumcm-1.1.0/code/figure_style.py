# File: code/figure_style.py
"""Shared, reproducible typography for all manuscript data figures."""
from pathlib import Path
import logging
import warnings

import matplotlib as mpl
from matplotlib import font_manager


def configure_fonts() -> None:
    """Require the actual regular fonts, rather than a platform-dependent fallback."""
    for family in ("Times New Roman", "SimSun"):
        path = font_manager.findfont(
            font_manager.FontProperties(family=family, weight="normal", style="normal"),
            fallback_to_default=False,
        )
        resolved = font_manager.get_font(path)
        if resolved.family_name != family or resolved.style_name != "Regular":
            raise RuntimeError(
                f"Expected {family} Regular; resolved {resolved.family_name} "
                f"{resolved.style_name} at {path}"
            )
    mpl.rcParams.update({
        "font.family": ["Times New Roman", "SimSun"],
        "font.weight": "normal",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.labelweight": "normal",
        "axes.titlesize": 11,
        "axes.titleweight": "normal",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "legend.title_fontsize": 10,
        "figure.titlesize": 12,
        "figure.titleweight": "normal",
        "mathtext.fontset": "custom",
        "mathtext.rm": "Times New Roman",
        "mathtext.it": "Times New Roman:italic",
        "mathtext.bf": "Times New Roman:bold",
        "mathtext.sf": "Times New Roman",
        "mathtext.fallback": "stix",
        "axes.unicode_minus": True,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def save_figure(fig, filename) -> None:
    """Export embedded-font PDF and PNG; never silently accept missing glyphs."""
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    from matplotlib.text import Text

    # Non-math Chinese runs need an explicit face; $...$ keeps Times math.
    for text in fig.findobj(Text):
        value = text.get_text()
        if "$" in value and any("\u3400" <= ch <= "\u9fff" for ch in value):
            text.set_fontfamily("SimSun")

    class MissingGlyphError(logging.Handler):
        def emit(self, record):
            message = record.getMessage()
            if "does not have a glyph" in message or "dummy symbol" in message:
                raise RuntimeError(message)

    logger = logging.getLogger("matplotlib")
    guard = MissingGlyphError()
    logger.addHandler(guard)
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error", message=r"Glyph .* missing from font")
            fig.canvas.draw()
            for suffix in ("pdf", "png"):
                fig.savefig(f"{filename}.{suffix}", bbox_inches="tight", dpi=300)
    finally:
        logger.removeHandler(guard)
