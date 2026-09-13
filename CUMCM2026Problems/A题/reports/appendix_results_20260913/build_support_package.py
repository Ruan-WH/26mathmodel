"""Build the current submission package with all appendix-B Python sources."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    current = Path(__file__).resolve().parent.parent / "python_delivery_20260913" / "build_support_package.py"
    runpy.run_path(str(current), run_name="__main__")
