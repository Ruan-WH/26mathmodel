# COMSOL 自动化复现：问题一

本目录把 A 题问题一的固定半径 Fourier–Fick 模型写成 COMSOL Java API 模型。
二维计算域取半径 0.02 m、轴向厚度 0.001 m 的绝热切片，并在通用 PDE 的储存项、扩散项和表面通量中显式乘以径向坐标，严格实现圆柱径向守恒形式。两端零通量使解沿轴向保持一致。

边界环境数据由 `prepare_inputs.py` 从附件 1 读取，经 PCHIP 插值后按 1 s 采样。
圆柱侧表面同时施加温度和水分 Robin 边界；轴线与两端采用自然零通量条件。

预期产物：

- `q1_comsol_model.mph`：可在 COMSOL 6.3 中打开的已求解模型；
- `q1_comsol_profiles.csv`：8 个时刻、21 个半径位置的温度与水分；
- `comsol_compile.log`、`comsol_batch.log`：编译与求解日志；
- `comparison.json`：与项目基准结果的比较信息。

## 已验证结果

COMSOL 6.3.0.290 批处理求解成功。对正文采用的 7 个时刻、5 个半径位置共 35 个点进行比较：

- 温度最大绝对差：0.002163 °C；RMSE：0.001492 °C；
- 水分浓度最大绝对差：0.000493 kg/kg；RMSE：0.000115 kg/kg。

1800 s 时，COMSOL 的中心/表面温度为 33.5751/36.7844 °C，中心/表面水分浓度为 2.5500/1.5102 kg/kg。

## 复现

在 PowerShell 中运行 `run_comsol_q1.ps1`。脚本重新准备边界数据、编译 Java API 模型、批量求解并生成比较表。
