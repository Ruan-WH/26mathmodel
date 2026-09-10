---
name: doctor
description: "手动检查逐题数学建模工作流所需的 Python、LaTeX、DrawIO 和 PDF 渲染环境；只在用户确认后安装缺失依赖。"
allowed-tools: Bash(*), Read, Write
---

# 环境检查

只在用户显式调用时运行。检测操作系统和可用命令，不修改项目、不静默安装。

## 必查

- Python 3 及 `numpy`, `pandas`, `matplotlib`。
- 按题型检查 `scipy`, `scikit-learn`, `openpyxl` 等实际需要的包。
- `xelatex` 与 `latexmk`：指定 CUMCM 模板的编译环境。
- `drawio`/`draw.io`：非数据图导出。
- `pdftoppm`、`mutool` 或 `magick` 至少一个：PDF 视觉检查。

输出版本、路径和 `OK/MISSING/OPTIONAL` 表。区分会阻断当前任务的依赖与暂时不需要的可选项。

若缺失依赖，先给出适合当前平台的精确安装命令、下载规模和权限影响，再请求用户明确确认。用户未确认不得执行安装。安装后重新检测并报告仍受限的环节。

Windows 优先检测 `py`、`python`、MiKTeX/TeX Live、DrawIO Desktop 与 Poppler；Linux/macOS 使用平台包管理器，但涉及 sudo、网络下载或系统目录写入时必须先获授权。
