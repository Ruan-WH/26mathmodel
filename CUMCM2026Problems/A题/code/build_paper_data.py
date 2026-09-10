"""Generate manuscript numbers/tables from final numerical results, then sync assets."""
from pathlib import Path
import json
import math
import shutil
import numpy as np
import solve_drying as s

PAPER=s.ROOT/'paper/cumcm-1.1.0'
OUT=PAPER/'contents/generated'


def read(name):
    return json.loads((s.RESULTS_DIR/name).read_text(encoding='utf-8'))


def sci(value):
    if value==0:
        return '0'
    mantissa,exponent=f'{value:.2e}'.split('e')
    return '$'+mantissa+r'\times10^{'+str(int(exponent))+'}$'


def table(name,caption,header,rows,label=None,small=False):
    text=r'\begin{table}[!htbp]\centering'+'\n'
    if small:
        text+=r'\small'+'\n'
    text+=r'\caption{'+caption+'}'
    if label:
        text+=r'\label{'+label+'}'
    text+='\n'+r'\begin{tabular}{'+'l'+'r'*(len(header)-1)+'}'+r'\toprule'+'\n'
    text+=' & '.join(header)+r'\\\midrule'+'\n'
    text+='\n'.join(' & '.join(map(str,row))+r'\\' for row in rows)
    text+='\n'+r'\bottomrule\end{tabular}\end{table}'+'\n'
    (OUT/(name+'.tex')).write_text(text,encoding='utf-8')


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    summaries={q:read(f'q{q}/summary.json') for q in [1,2,3,4]}
    for q in [1,2]:
        summary=summaries[q]
        times=summary['table_times_s' if q==1 else 'table_times_h']
        for variable in ['temperature','moisture']:
            values=summary['temperature_table_c' if variable=='temperature' else 'moisture_table']
            rows=[[str(t) if q==1 else f'{t:.1f}']+[f'{v:.4f}' for v in row] for t,row in zip(times,values)]
            table(f'q{q}_{variable}',f'问题{q}'+('温度分布（$^\\circ$C）' if variable=='temperature' else '含水率分布（kg/kg）'),
                  ['$t$/'+('s' if q==1 else 'h'),'0 cm','0.5 cm','1.0 cm','1.5 cm','2.0 cm'],rows)
    for q in [3,4]:
        summary=summaries[q]
        rows=[[f'{t:.4f}' if i==len(summary['table_times_h'])-1 else f'{t:.0f}']+
              ['---' if v is None else f'{v:.4f}' for v in row]
              for i,(t,row) in enumerate(zip(summary['table_times_h'],summary['moisture_table']))]
        header=['$t$/h','0 cm','0.5 cm','1.0 cm']+(['1.5 cm','2.0 cm'] if q==3 else ['动态表面'])
        table(f'q{q}_moisture',f'问题{q}每6 h及达标时含水率（kg/kg）',header,rows)
    numbers={'SolverNodes':str(s.NODES)}
    for q,word in [(1,'Qone'),(2,'Qtwo')]:
        sm=summaries[q]
        numbers.update({word+'CenterT':f"{sm['temperature_table_c'][-1][0]:.4f}",
                        word+'SurfaceT':f"{sm['temperature_table_c'][-1][-1]:.4f}",
                        word+'CenterC':f"{sm['moisture_table'][-1][0]:.4f}",
                        word+'SurfaceC':f"{sm['moisture_table'][-1][-1]:.4f}"})
    for q,word in [(3,'Qthree'),(4,'Qfour')]:
        sm=summaries[q]
        numbers.update({word+'Hours':f"{sm['drying_time_h']:.4f}",word+'Seconds':f"{sm['drying_time_s']:.4f}",
                        word+'SurfaceC':f"{sm['moisture_table'][-1][-1]:.4f}",
                        word+'OutputEnd':str(int(sm['output_end_s']))})
    fixed=summaries[4]['fixed_radius_counterfactual']
    numbers.update(QfourFixedHours=f"{fixed['same_appendix4_properties_time_h']:.4f}",
                   QfourReduction=f"{100*fixed['relative_reduction']:.2f}",
                   QfourRadius=f"{summaries[4]['radius_at_end_cm']:.4f}")
    grid=read('graded_grid_study.json')
    by_grid={(x['nodes'],x['q']):x['time_h'] for x in grid}
    assert all((n,q) in by_grid for n in [81,161,321,641] for q in [3,4]), 'Incomplete spatial study'
    table('grid','表面加密网格下的首达时间（h）',['节点数','问题三','问题四'],
          [[n,f'{by_grid[n,3]:.6f}',f'{by_grid[n,4]:.6f}'] for n in sorted({x['nodes'] for x in grid})])
    checks=read('field_verification.json')
    rows=[]
    for q in [3,4]:
        sm=summaries[q];half=sm['time_step_check']['dt5_s_time_h'];early=checks[f'q{q}_early_dt_half']
        rows.append([f'问题{q}',f"{sm['drying_time_h']:.6f}",f'{half:.6f}',
                     f"{abs(half-sm['drying_time_h'])*3600:.3f}",f"{abs(early['difference_s']):.3f}"])
    table('time','分阶段时间步变化的首达检验',['情形','基准/h','后段5 s/h','后段差/s','前段减半差/s'],rows,small=True)
    rows=[]
    for q in [1,2]:
        ck=checks[f'q{q}_321_vs_641']
        rows.append([f'问题{q}：321与641节点',sci(ck['max_abs_T']),sci(ck['max_abs_C'])])
    ck=checks['q2_q3_shared_prefix']
    rows.append(['问题二、三共同时间点',sci(ck['max_abs_T']),sci(ck['max_abs_C'])])
    table('field_checks','场量网格差与前段一致性',['比较量','温度最大差/$^\\circ$C','含水率最大差/kg/kg'],rows,small=True)
    rows=[]
    for q in [1,2,3,4]:
        ck=read(f'q{q}/diagnostics.json')
        assert ck['nodes']==s.NODES and ck['grid_power']==s.GRID_POWER
        rows.append([f'问题{q}',sci(ck['maximum_step_mass_residual']),sci(ck['relative_cumulative_mass_residual'])])
    table('conservation','归一化干基质量平衡残差',['情形','最大单步残差/kg/kg','相对累计残差'],rows)
    benchmark=read('independent_numerics.json')
    assert benchmark['all_pass']
    numbers.update(EigenError=sci(benchmark['bessel_robin_eigenmode'][-1]['max_abs_error']),
                   FluxError=sci(benchmark['kirchhoff_quadrature_max_relative_error']),
                   ClosedError=sci(benchmark['closed_uniform_shrinkage_max_error']))
    twod=read('validation_2d_long.json')
    assert {(q,41,nz,60) for q in [3,4] for nz in [31,61]} <= {
        (v['question'],v['radial_nodes'],v['half_axial_nodes'],v['dt_s']) for v in twod
    }, 'Incomplete long-duration axial refinement'
    rows=[]
    for ck in twod:
        assert ck['grid_power']==s.GRID_POWER
        if ck['question']==1:
            continue
        rows.append([ck['question'],f"{ck['radial_nodes']} x {ck['half_axial_nodes']}",ck['dt_s'],
                     f"{ck['drying_time_1d_h']:.5f}",f"{ck['drying_time_2d_h']:.5f}",f"{ck['difference_s']:.3f}"])
    table('twod','二维全域与同设置一维首达比较（前段10 s）',['问题','径向×半轴向','后段/s','一维/h','二维/h','差/s'],rows,small=True)
    scenarios=read('sensitivity.json')
    assert len(scenarios)==11, 'Incomplete sensitivity scenarios'
    labels={'baseline':'同设置基准','temperature_minus_2C':'末端温度 $-2~^\\circ$C','temperature_plus_2C':'末端温度 $+2~^\\circ$C',
            'ambient_moisture_minus_5pct':'末端含湿量 $-5\\%$','ambient_moisture_plus_5pct':'末端含湿量 $+5\\%$',
            'diffusivity_minus_5pct':'扩散倍率 $-5\\%$','diffusivity_plus_5pct':'扩散倍率 $+5\\%$',
            'mass_transfer_minus_5pct':'传质系数 $-5\\%$','mass_transfer_plus_5pct':'传质系数 $+5\\%$',
            'shrinkage_amplitude_minus_5pct':'收缩幅度 $-5\\%$','shrinkage_amplitude_plus_5pct':'收缩幅度 $+5\\%$'}
    table('sensitivity','敏感性试验（81节点；前段2 s、后段20 s）',['情景','问题三/h','问题四/h'],
          [[labels[k],f"{v['q3_drying_time_h']:.4f}",f"{v['q4_drying_time_h']:.4f}"] for k,v in scenarios.items()])
    (OUT/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+key+'}{'+value+'}' for key,value in numbers.items())+'\n',encoding='utf-8')
    for code in (s.ROOT/'code').glob('*.py'):
        shutil.copy2(code,PAPER/'code'/code.name)
    for figure in (s.ROOT/'figures').glob('*.pdf'):
        shutil.copy2(figure,PAPER/'figures'/figure.name)
    for figure in (s.ROOT/'drawio').glob('*.pdf'):
        shutil.copy2(figure,PAPER/'figures'/figure.name)
    print('Generated all manuscript numbers and tables; synchronized source code and figures.')

if __name__=='__main__':
    run()
