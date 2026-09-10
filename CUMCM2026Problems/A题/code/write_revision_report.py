"""Summarize the final revision without treating older reports as current evidence."""
import json
from pathlib import Path
import solve_drying as s


def read(name):
    return json.loads((s.RESULTS_DIR/name).read_text(encoding='utf-8'))


def run():
    q3=read('q3/summary.json');q4=read('q4/summary.json')
    grid=read('graded_grid_study.json');fields=read('field_verification.json')
    grid={(row['nodes'],row['q']):row['time_h'] for row in grid}
    twod=read('validation_2d_long.json');counter=q4['fixed_radius_counterfactual']
    report=f'''# A题本轮修改与验证记录

本报告对应2026-09-10的修订。旧报告中的21节点结果和旧移动项分析属于历史记录，当前结果以本报告及 `results/q*/summary.json` 为准。

## 已执行的修改

- 以均匀径向材料收缩推导第四问：材料速度与网格速度相同，相对对流项为零；区分干物质质量权重和题给经验热物性密度。
- 内部采用321个表面加密节点，映射 `ξ=1-(1-u)^2`。题目的0.1 cm间距只用于输出。
- 对含水率指数扩散率使用Kirchhoff积分型界面通量，保留对温度及空间几何的近似。
- 第一、二问逐秒计算；第三、四问前3 h为1 s、后段10 s。按全截面最大含水率插值定位首达事件。
- 增加空间、分阶段时间、解析模态、封闭收缩、质量平衡和长期二维验证。更新温度±2°C、含湿量/扩散/传质/收缩幅度±5%的情景分析。
- 正文数值和表格从JSON自动生成；更新科学图、可编辑流程图、AI使用说明、附录复现入口和论文代码副本。

## 当前数值结果

| 指标 | 修订结果 |
|---|---:|
| 第三问首达时间/h | {q3['drying_time_h']:.8f} |
| 第四问首达时间/h | {q4['drying_time_h']:.8f} |
| 第四问同物性固定半径对照/h | {counter['same_appendix4_properties_time_h']:.8f} |
| 对固定半径对照的条件性缩短 | {100*counter['relative_reduction']:.4f}% |
| 第四问达标半径/cm | {q4['radius_at_end_cm']:.4f} |

旧结果第三问56.186319 h、第四问51.985713 h不应继续用于本次修订的摘要、表格或结论。新旧差异同时涉及网格/通量和第四问模型修订，不能全部归因于单一因素。

## 数值证据与精度边界

| 比较 | 第三问/s | 第四问/s |
|---|---:|---:|
| 321与641节点首达差 | {abs(grid[321,3]-grid[641,3])*3600:.6f} | {abs(grid[321,4]-grid[641,4])*3600:.6f} |
| 3 h以后10 s改5 s的首达差 | {abs(q3['drying_time_h']-q3['time_step_check']['dt5_s_time_h'])*3600:.6f} | {abs(q4['drying_time_h']-q4['time_step_check']['dt5_s_time_h'])*3600:.6f} |
| 前3 h的1 s改0.5 s的首达差 | {abs(fields['q3_early_dt_half']['difference_s']):.6f} | {abs(fields['q4_early_dt_half']['difference_s']):.6f} |

第一、二问321与641节点在共同位置的最大含水率差分别为 {fields['q1_321_vs_641']['max_abs_C']:.3e}、{fields['q2_321_vs_641']['max_abs_C']:.3e} kg/kg。第二、三问共同时间点的温度、含水率最大差分别为 {fields['q2_q3_shared_prefix']['max_abs_T']:.3e}、{fields['q2_q3_shared_prefix']['max_abs_C']:.3e}。

这些是离散解之间的差异，不是真解误差界。后段步长差仍约十余秒，故首达时间写四位小数仅是格式，不能据此声称达到0.0001 h物理精度。完整独立基准见 `results/independent_numerics.json`；四问归一化累计质量残差见各自 `diagnostics.json`。

## 长期二维检查

二维取半圆柱，中截面为z=0，暴露端面为z=L/2；与同径向网格、同时间步的一维模型比较。以下仅报告已经完成的计算。

| 问题 | 径向×半轴向节点 | 后段步长/s | 二维减一维/s | 首达控制点位于几何中心 |
|---|---|---:|---:|---|
'''
    for row in twod:
        if row['question']!=1:
            report+=f"| {row['question']} | {row['radial_nodes']}×{row['half_axial_nodes']} | {row['dt_s']} | {row['difference_s']:.6f} | {row['maximum_at_radial_axial_center']} |\n"
    report+='''
此对照估计本题几何下端面影响，不等同于真实药材实验验证。不得把短期1800 s检查单独作为长期首达依据。本轮完成半轴向31→61节点加密，二维径向为41节点、前段10 s、后段60 s；若要精确解释数秒差异，仍需完整二维径向与时间加密，可运行 `validate_long.py --extended`。一维收敛检验不能替代二维的全面收敛分析。

## 参考文献与待扩展内容

已阅读全文并核对根目录 `paper` 的三篇PDF，详细对照见工作区 `output/review/三篇参考文献对照与后续改进.md`。第三篇是8页会议稿，文献身份已按正文及作者机构资料核对。

后续优先做表面蒸发潜热、材料平衡吸湿关系和一致能量闭合的对照；本轮主结果没有引入未标定的潜热项。现有经验密度、给定半径和均匀收缩并非严格混合物闭合；恒定延拓环境也是情景假设。不要移植其他材料的物性、红外热源或“最优温度”。

## 复现与交付状态

从A题外层运行 `python code/reproduce.py`；它会按顺序计算、核验并生成正文数据。完整验证涉及长时间二维计算。用XeLaTeX/latexmk或Tectonic编译 `paper/cumcm-1.1.0/main.tex`。本机采用Tectonic并检查PDF页面。

四份Excel导出脚本已适配细网格、物理位置采样与逐单元格回读检查，但本轮尚未运行：电子表格技能规定的artifact-tool不可用，复用仓库openpyxl需要用户明确选择。目前 `results/result*.xlsx` 仍是旧版，不要与新稿一起提交。收到许可后运行 `python code/write_results.py`，再核对 `workbook_verification.json` 全部通过。
'''
    verification=read('workbook_verification.json')
    workbooks_current=all((s.RESULTS_DIR/f'result{q}.xlsx').stat().st_mtime >=
                          (s.RESULTS_DIR/f'q{q}/fields.npz').stat().st_mtime for q in [1,2,3,4])
    workbooks_current=workbooks_current and all(item['pass'] for item in verification['verification'])
    if workbooks_current:
        report=report[:report.index('四份Excel导出脚本已适配')]+ '四份Excel已经从当前终算数据重新导出，回读验证全部通过。记录见 `results/workbook_verification.json`。\n'
    (s.ROOT/'reports/REVISION_REPORT.md').write_text(report,encoding='utf-8')


if __name__=='__main__':
    run()
