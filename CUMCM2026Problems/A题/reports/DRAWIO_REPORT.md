# DrawIO 图示报告

## 2026-09-13 图 2 题注回置（当前版本）

删除上下分图间横线，(a)、(b) 题注改为各分图下方居中；中截面辅助虚线适度减淡。源图、生成器、论文插图、附录代码及支撑包已同步，正文第 6 页图 2 检查通过，正文仍为 30 页。详细记录见 `GEOMETRY_DIAGRAM_QA.md`。

## 2026-09-13 图 2 版式优化

重新对齐分图标题、尺寸和边界标注，以灰色分隔线区分两部分；保留圆柱比例、坐标和物理含义，更新源图、PDF、PNG及论文第 6 页图 2。绘图生成器、附录副本和支撑材料内对应文件已同步。正文仍为 30 页，详细检查见 `GEOMETRY_DIAGRAM_QA.md` 最新记录。

## 2026-09-13 图 10 圆角与返回连线调整

- 修改 `moving_boundary_solver.drawio` 的四个处理框：统一 `rounded=1;absoluteArcSize=1;arcSize=24`，使用固定 12 px 圆角半径，避免不同框高造成圆角大小不一致。节点文字、位置和尺寸不变。
- 右侧“否”分支明确从阈值判断框右侧中点出发，返回 PCHIP 更新框右侧中点，折点高度分别与两节点中点一致。
- 使用 DrawIO CLI crop 导出 PDF，更新 `drawio/` 中 PDF、PNG 及论文 `figures/` 中 PDF；核对独立预览与论文第 23 页图 10，圆角一致、返回箭头落点正确。
- 两遍 XeLaTeX 编译通过，无越界、缺失字符或未解析引用。正文仍为 30 页，全文 78 页；逐页渲染比较仅第 23 页发生变化。检查记录在 `D:/26mathmodel/tmp/flow_rounding/checks.json`，临时解包的 DrawIO 运行文件已清理。

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

## 药材几何与坐标系增补

新增 drawio/geometry_coordinates.drawio 及 PDF、PNG，插入模型准备的几何降维小节，当前为图 2（第 7 页）。图示包含 25 cm 长、2 cm 初始半径的圆柱、坐标轴、中截面放大、径向计算域及预热传热传质方向。源图、字体嵌入、几何比例、正文位置和编译验收详见 GEOMETRY_DIAGRAM_QA.md；其余既有图未改变。
