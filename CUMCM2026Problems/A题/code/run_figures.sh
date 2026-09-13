#!/bin/zsh
# Rebuild all data-driven figures with the repository's fixed font environment.
set -euo pipefail
SCRIPT_DIR="${0:A:h}"
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$HOME/.matplotlib-cumcm2026}"
mkdir -p "$MPLCONFIGDIR"
cd "$SCRIPT_DIR/.."

python3 - <<'PY'
from matplotlib import font_manager
font_manager._load_fontmanager(try_read_cache=False)
for name in ("Times New Roman", "Songti SC"):
    print(f"{name}: {font_manager.findfont(name, fallback_to_default=False)}")
PY

python3 "$SCRIPT_DIR/make_figures.py"
if python3 -c 'import openpyxl' >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/make_additional_figures.py"
else
    echo "提示：当前 Python 缺少 openpyxl，已完成基础图；运行附加图前请安装 openpyxl。" >&2
fi
