> 修订状态说明（2026-09-10）：本文件保留为旧版记录，旧结果、图表和验收声明不代表当前版本；请以[本轮修改与验证记录](REVISION_REPORT.md)为准。

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
