---
name: mathmodel-figure-templates
description: "在 3coding-visual 与 academic-figure-skill 已确定图形契约后，为数学建模数据图选择和复用合适的科研绘图结构；不以模板外观替代证据设计。"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

# 科研绘图模板

模板脚本位于 `scripts/templates/`，目录映射见 `references/figure-catalog.md`，实现思路见 `references/plot-recipes.md`。

## 使用

1. 先由 `3coding-visual` 确认数据、模型量和结论，再按 [academic-figure-skill 的图形契约](../academic-figure-skill-main/academic-figure-skill-main/references/figure-contract.md) 确定证据层级和面板职责；没有图形契约时不直接套模板。
2. 根据要回答的科学问题选择最接近的模板，并先扫描 `academic-figure-skill-main/academic-figure-skill-main/assets/figures/`。若没有语义与数据结构兼容的资产，按 `param inherit` 或 `cross-type inherit` 设计新图，不为复用而牺牲可读性。
3. 先复制模板脚本到当前项目的 `code/` 或绘图脚本目录，再修改副本；不要改本 skill 的基准模板，也不要直接运行模板的模拟数据作为论文结果。
4. 用项目真实数据替换模拟数据。若只做模板演示，必须在图内或说明中明确标注为模拟数据。
5. 保留确定性随机种子、数据追溯、可编辑文字和紧凑布局技巧；默认输出矢量 PDF 和 300 dpi PNG，具体标准服从 `academic-figure-skill`。
6. 服从 `3coding-visual/references/academic-visual-style.md` 的数学建模语义与 `academic-figure-skill` 的资产确认、视觉和四阶段 QA 规则，不机械复制模板中的标题、颜色、字号、宽高比或示例数值。

模板只提供复杂图层结构，如原始点+分布+摘要、折间曲线+置信带、主散点+边缘分布、多面板共享图例。使用后仍需删除冗余面板，并按论文最终尺寸、灰度辨识、字体嵌入和矢量文字完成视觉验收。
