# 数学建模 × Academic Figure 融合规范

本文件连接 `3coding-visual` 与 `academic-figure-skill-main`。数学模型、真实计算结果和约束口径由前者负责；图形契约、资产确认、证据组织、投稿级视觉与 QA 由后者负责。不得用示例资产中的模拟数据替换项目结果，也不得为了套模板重复表达同一结论。

## 必读路由

1. 完整读取 [academic-figure-skill-main/SKILL.md](../../academic-figure-skill-main/academic-figure-skill-main/SKILL.md)。
2. 每次作图读取该 skill 的 `references/figure-contract.md`、`color-palettes.md`、`typography.md`、`journal-specs.md`、`export-specs.md` 和 `checklist.md`。
3. Python 项目继续读取 `references/matplotlib.md`；多面板图读取 `references/multipanel-layout.md`；交付前读取 `references/common-pitfalls.md`。
4. 必须先扫描 `assets/figures/`，在脚本导入语句之前写 Asset Confirmation Table。只有语义与数据结构都兼容时才复制并原生运行资产；否则明确写 `param inherit` 或 `cross-type inherit`，只继承视觉参数或图层结构。

当前项目已有 Python 求解与绘图脚本，因此沿用 Python，不再询问后端。

## 数学建模图形契约

每张图在编码前明确：一句话核心结论、主证据、验证证据、每个面板的独立职责、最终宽度、数据文件、约束或区间定义以及最可能被质疑的口径。多面板采用一个主面板带一个辅助面板，能删则删，不用柱图和时间轴重复同一组数字。

确定性优化结果通常没有抽样意义上的误差条。验证证据应来自多起点/多随机种子收敛、离散精度、可行性余量、灵敏度、边际贡献或算法对照；不得伪造置信区间、显著性检验或样本重复。

## 视觉与导出底线

- 优先采用 academic skill 的受控蓝、红、绿、橙、紫和中性灰色板；同一对象跨图保持一致，不能只靠颜色区分。
- 使用开放坐标轴、细轴线、克制网格和直接标注；不放论文式大标题，不使用渐变、阴影、装饰性 3D 或彩虹色。
- CUMCM 数据图的英文、阿拉伯数字和公式使用 Times New Roman，中文使用 SimSun。Matplotlib 设置 `font.family=["Times New Roman", "SimSun"]`，不得把 SimSun 置于首位；数学字体显式映射到 Times New Roman。缺少任一字体时停止导出并报告，不静默替换。
- 多面板编号 `(a)`、`(b)` 等放在对应子图下方水平居中位置，且与横轴标题、图下注释保持清晰间距；禁止放在左上角。
- 通栏图以 183 mm、单栏图以 89 mm 为基准；最终字号不小于 5 pt，常规刻度 7 pt、轴标签 8 pt。
- 脚本保留 skill 要求的 Typography、Color Palette 和 Export Baseline 原文块；从同一 Figure 对象导出矢量 PDF 与 300 dpi PNG。
- 交付前依次完成资产来源检查（AP）、代码静态检查（CL）、成图视觉检查（VI）和图文一致性检查（VV），并记录数据来源、样本/迭代定义、统计方法或“不适用”的理由。
