from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
s=json.loads((HERE/'summary.json').read_text(encoding='utf-8'))
rows=s['cases'];best=next((r for r in rows if r['case']=='graded320_tight'),rows[-1])
lines=['# COMSOL 近表层网格与容差检验（独立试算）','',
'本目录为独立试算，未修改论文、原 COMSOL 模型或四问主计算结果。',
'','## 检验设置','',
'- 各组既有计算采用相同的物性、系数型 PDE、初值、Robin 边界、半径及环境输入文件。',
'- 保持原参考矩形长度 0.08 m、轴向均匀和端面绝热；这不是含端面交换的二维验证。',
'- 原网格采用 autoMeshSize(3)。加密组使用映射四边形网格，径向 80/160/320 单元、轴向 4 单元，径向端点按 (1-cos(pi*i/N))/2 分布，在轴线与表层加密。',
'- 相对求解容差按表设置；仍为自适应时间求解，输出间隔不是固定积分步长。',
'- 与主模型在 6、12、24、36、48 h 及 51.0876993 h 比较；每时刻 1001 个共同径向位置（包括表面），主模型用全部 161 个原生节点线性插值。',
'- 所有“最大差”均针对上述六时刻/采样位置，不能解释为全时空的严格误差界。',
'','## 与主有限体积结果比较','',
'| 试算 | 径向单元 | 相对容差 | 最大水分绝对差 kg/kg | 时刻 h | r/R |',
'|---|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {r['case']} | {r['radial_elements']} | {r['rtol']} | {r['max_moisture_difference']:.8g} | {r['at_time_h']:.4f} | {r['at_xi']:.3f} |")
lines+=['','## COMSOL 自身网格与容差变化','',
'| 比较 | 最大水分差 kg/kg | 最大温差 °C |','|---|---:|---:|']
for r in s['successive_comparisons']:lines.append(f"| {r['a']} → {r['b']} | {r['max_moisture_difference']:.8g} | {r['max_temperature_difference']:.8g} |")
lines+=['','## 结果解释','',
'收紧原网格容差后，约 0.0117 kg/kg 的近表层偏差仍存在；使用表层加密网格后，偏差降至约 10^-5 kg/kg 量级。这支持原 COMSOL 网格的近表层分辨能力是原偏差的主要来源。',
'','加密组对有限体积结果的最大差不必随网格单调减小：比较基准本身仍有时间、空间离散误差和线性插值误差。因此应同时看 COMSOL 相邻网格之间的差异，不能把两法之差当成 COMSOL 的真实误差。',
'',f"最细且更紧容差组在主模型达标时刻的中心水分为 {best['center_C_at_FVM_event']:.10f} kg/kg，表面水分为 {best['surface_C_at_FVM_event']:.10f} kg/kg。",
'',f"按已保存输出线性插值得到的 COMSOL 达标时间估计为 {best['estimated_COMSOL_event_h']:.8f} h；此值不是内部事件求根结果，不应据此宣称秒以下的预测精度。",
'','两法计算输入一致性不等同于实验准确性验证；本次沿用原 COMSOL 的线性插值输入文件，未将其与主程序 PCHIP 之间的细微差异一并消除。',
'','## 文件与复核','',
'- 各子目录：batch.log、COMSOL 原始 CSV、包含解的 q4_shrinking_herb_comsol.mph。',
'- comparison.csv / summary.json：数值比较与逐时刻最大差。',
'- comparison_fields.npz：六时刻的共同采样场与有限体积参考。',
'- analyze_refinement.py：重新读取原始导出并比较；write_report.py：生成本报告。',
'- manifest.json：运行设置与受保护文件的原始 SHA256。',
'',f"受保护文件保持不变：{all(s['protected_files_unchanged'].values())}。",
'','网格 API 依据：[COMSOL 6.3 Distribution](https://doc.comsol.com/6.3/doc/com.comsol.help.comsol/comsol_api_mesh.49.073.html)、[Map](https://doc.comsol.com/6.3/doc/com.comsol.help.comsol/comsol_api_mesh.49.090.html)。']
(HERE/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
