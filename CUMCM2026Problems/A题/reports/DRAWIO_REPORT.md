# DrawIO 图示报告

## 总体技术路线图

- 源文件：`drawio/overall_roadmap.drawio`
- 导出：`drawio/overall_roadmap.pdf`、`drawio/overall_roadmap.png`
- 正文位置：问题分析，图 1。
- 字体处理：中文节点显式指定 SimSun；`PCHIP`、`Fourier--Fick`、`Robin` 显式指定 Times New Roman。
- 验收：黑白灰、正交连线、无穿越节点；独立 PNG 与论文第 2 页均已检查。

## 移动边界求解流程图

- 源文件：`drawio/moving_boundary_solver.drawio`
- 导出：`drawio/moving_boundary_solver.pdf`、`drawio/moving_boundary_solver.png`
- 正文位置：问题四固定域变换，图 5。
- 字体处理：中文显式指定 SimSun；英文、数字、希腊变量和公式显式指定 Times New Roman，其中变量使用 Times New Roman Italic。
- 乱码修复：移除不稳定的组合重音 `Ṙ`，改写为等价的 `(dR/dt)`；`c_p` 使用 HTML 下标，`ξ=r/R(t)` 与阈值公式使用富文本混排。
- 验收：PDF 字体清单仅含 SimSun、TimesNewRomanPSMT、TimesNewRomanPS-ItalicMT，全部嵌入；不再包含 Noto/替代字体。独立 PNG 与论文第 9 页均已检查，无乱码、裁切或重叠。

## 2026-09-11 局部修订

仅修改移动边界图的方程说明及 Picard 返回分支，保留原有位置、形状和字体。材料速度与网格速度相同，相对输运为零；未收敛分支返回物性更新节点。使用完整 DrawIO 26.0.16 运行文件以 `-x -f pdf --crop` 导出，PDF 渲染为 PNG，并复核正文第 21 页，无文字重叠或连线穿过节点。便携启动器资源不全时产生的中间错误 PDF 已替换，未作为最终成果。
