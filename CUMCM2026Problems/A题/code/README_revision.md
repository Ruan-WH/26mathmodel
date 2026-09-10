# 修订版复现

权威入口为A题外层code；论文内code是归档副本。

```powershell
python code/reproduce.py
```

依赖Python、numpy、scipy、openpyxl（读取题给Excel）、matplotlib；绘图使用Times New Roman和SimSun字体。运行前保留原始附件目录。复现包含全部终算、独立核验、轴向加密的长期二维试验和敏感性，可能耗时较长。可运行 `python code/validate_long.py --extended` 增加二维径向与时间步加密，此扩展不属于当前终算证据。

显式选择导出工作簿时使用 `python code/reproduce.py --workbooks`，或在终算数据已有时运行 `python code/write_results.py`。应确认回读验证全部通过。

图表和正文数值由 `build_paper_data.py` 同步，使用XeLaTeX/latexmk或Tectonic编译 `paper/cumcm-1.1.0/main.tex`。当前本机使用Tectonic 0.15.0。
