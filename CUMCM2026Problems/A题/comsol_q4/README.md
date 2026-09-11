# 第四问 COMSOL 收缩药材仿真

本目录给出一个可直接打开验证的 COMSOL 6.3 模型，以及由 COMSOL 解导出的论文级物理场图。模型把药材视为轴向均匀、端面绝热的圆柱，代表长度取 8 cm；长度不参与径向解，药材初始半径为 2 cm，并按附件 2 的单调 PCHIP 半径曲线收缩。

## 打开与查看

1. 在 COMSOL 6.3 中打开 `q4_shrinking_herb_comsol.mph`。
2. 展开“结果”，选择 `Moisture field in shrinking herb reference domain` 或 `Temperature field in shrinking herb reference domain`。
3. 点击工具栏“绘制”。模型已经包含 0–183000 s 的瞬态解，无需重新计算即可查看。
4. 若要复算，右键“研究 1”选择“计算”；环境温湿度和半径函数文件必须与 MPH 文件放在同一目录。

COMSOL 内部使用初始材料半径作为参考坐标，变量 `rphys=x*Rt(t)/R0` 是相应的实际物理半径。论文图 `q4_comsol_physical_moisture_field.png` 已将径向有限元解映射回每个时刻的真实圆柱尺寸，所以可以直接看到收缩，而 COMSOL 默认的参考域表面图保持初始矩形外框。

## 方程与参数

- 状态物性：`rho=760+90C`，`cp=1850+2150C/(C+1)`，`k=0.12+0.20C/(C+1)`。
- 水分扩散率：`D=4.2e-4 exp(-0.30/C) exp[-3850/(T+273.15)] m²/s`。
- 初值：`T=28 °C`，`C=2.55 kg/kg`。
- 圆柱侧面：`hT=25 W/(m²·K)`，`hm=8e-7 m/s`；环境函数来自附件 1，4 h 后保持末值。
- 收缩解释：均匀材料收缩，固定材料坐标内无相对对流项，扩散项和边界通量按 `R0/R(t)` 缩放。

## 主要结果

- 第四问判据时刻：50.8213346 h。
- 此时半径：1.200 cm。
- COMSOL 中心含水率：0.149995 kg/kg；表面含水率：0.052060 kg/kg。
- 与原有限体积模型在六个校核时刻、101 个径向点比较，最大含水率绝对差为 0.004350 kg/kg；最大温度绝对差为 0.000418 °C。

`q4_comsol_validation.json` 和 `q4_comsol_comparison.csv` 保存校核数值，`q4_comsol_profiles.csv` 保存 COMSOL 原始导出数据。两张 PNG 用于直接查看，两张 PDF 是论文排版用矢量母版。
