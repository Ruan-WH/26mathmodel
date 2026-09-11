# 问题四直接移动网格独立验证

本目录结果来自真实的双路径积分：161 节点、1 s 时间步，共 183000 步。原主模型与 result4.xlsx 未修改。

## 复现

在 A题 目录运行（本机 Python 为 D:/Anaconda/python.exe）：

```powershell
& D:/Anaconda/python.exe code/validate_moving_mesh.py
& D:/Anaconda/python.exe code/plot_moving_mesh_validation.py
```

第一条独立推进两个状态并保存结果，本机耗时约 209 s；第二条读取实际结果生成图表。只检查基础物理性质可运行第一条并加 `--check-only`。原论文编译使用 paper/cumcm-1.1.0 中的 main.tex；绘图后用 XeLaTeX 编译两次。

## 文件

- `summary.json`：首达时刻、全程全节点最大差、Picard 次数、守恒残差。
- `comparison.csv` / `comparison_table_zh.md`：6、24、48 h 与达标时刻的中心/动态表面比较；相对差为绝对差除以固定域值，不是百分数。
- `profiles.csv`：6、24、48 h 及各自首达时刻完整 161 节点物理半径、水分、温度剖面。`own_event` 指各自达标时刻；`comparison.csv` 的 `common_event` 则在固定域首达时刻对两条逐秒轨迹独立插值，避免用两个恰为 0.15 的事件值代替同刻比较。
- `fields.npz`：逐分钟完整场和逐秒轨迹。`xi` 为 161 个节点标签；`times_s`、`radii_m` 为分钟帧坐标；`mapping_*` / `moving_*` 为两套场；`*_event_*` 为各自事件插值场。
- `step_trace` 列依次为：时间秒、固定域中心C、移动网格中心C、固定域表面C、移动网格表面C、全节点最大水分差、全节点最大温度差、中心水分绝对差。误差最大值由全部 183001 个时间层计算。
- `q4_moving_mesh_validation.pdf/png`：中心轨迹及24/48 h剖面；`q4_moving_mesh_errors.pdf/png`：逐秒全场差异，非统计不确定度。
- `unit_checks.json`：几何守恒、绝热绝湿收缩常值、静止网格退化检查。
- `reference_reproduction.json`：重算固定域结果与原结果的水分、温度、干燥时间差均为0。
- `protected_files_sha256.json`：计算前原始受保护文件哈希；绘图及最终交付再次核验这些原文件。

## 数值结果与理论边界

固定域 t_d=50.8213345750398 h，移动网格 t_d=50.8213345750672 h；绝对差9.86328814e-8 s，相对差5.39104745e-13。中心轨迹最大水分差8.93174423e-14 kg/kg，全场最大水分差2.61457522e-13 kg/kg，温度最大差1.14525278e-10 ℃。这些差值是两套离散实现之间的差，不是连续方程精确解误差，也不代表物理预测有这些有效位数。

采用材料速度等于网格速度的 ALE 闭合，运动对流通量因相对速度为零而消失；用干质量库存与物理面积/间距直接组装通量，同时核验几何扫掠守恒。热方程沿用有效 a D_t T 方程，其库存形式必须保留 T_old Δ(aV) 修正，不能宣称总焓无源守恒。详细推导见 [离散原理](../../../reports/Q4_MOVING_MESH_PRINCIPLE.md)。

在这些既有假设下，两套离散可代数互相对应，因此浮点量级的差异合理。这是独立几何/矩阵组装的数值互证，不是第二种物理机制或实验验证。一般 ALE 守恒与几何守恒原则参考 [Gaburro 等的原始论文](https://arxiv.org/abs/1602.01703)，本题一维离散由项目自行推导并检查。
