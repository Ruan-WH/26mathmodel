"""Render real Q4 validation data and generate the manuscript result table.

Asset confirmation: academic-figure-skill assets/figures/LineTrend/plot_sweep.py
was inspected; inherit open axes and overlaid line encoding, not example data.
Reuse the project's verified typography/palette/export baseline by import.
"""
import sys
sys.dont_write_bytecode = True
import csv
import json
import shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from make_additional_figures import CATEGORICAL
from figure_style import configure_fonts, save_figure
configure_fonts()
import matplotlib.pyplot as plt
from validate_moving_mesh import OUT, ROOT, write_comparisons, check_preservation


def render_figures(arrays):
    tr=arrays['step_trace']; hours=tr[:,0]/3600
    fig,axes=plt.subplots(1,2,figsize=(7.2,3.6))
    fig.subplots_adjust(left=.105,right=.98,bottom=.26,top=.96,wspace=.40)
    ax=axes[0]
    ax.plot(hours,tr[:,1],color=CATEGORICAL[0],lw=1.65,label='固定域映射法')
    ax.plot(hours,tr[:,2],color=CATEGORICAL[1],lw=1.0,ls=(0,(5,3)),label='直接移动网格法')
    ax.axhline(.15,color='#666666',ls=':',lw=.8)
    ax.text(5,.20,r'$C=0.15$',fontsize=10,color='#555555')
    ax.set(xlim=(0,52),ylim=(0,2.65),xlabel='时间 / h',ylabel='中心水分浓度 / (kg/kg)')
    ax.set_xticks([0,12,24,36,48]);ax.legend(loc='upper right',fontsize=10)
    ax.text(.5,-.30,'(a) 中心水分轨迹',transform=ax.transAxes,ha='center',fontsize=10)
    ax=axes[1]
    for h,color in [(24,CATEGORICAL[0]),(48,CATEGORICAL[4])]:
        i=int(np.flatnonzero(arrays['times_s']==h*3600)[0])
        r=100*arrays['radii_m'][i]*arrays['xi']
        ax.plot(r,arrays['mapping_moisture'][i],color=color,lw=1.65,label=f'{h} h，固定域')
        ax.plot(r,arrays['moving_moisture'][i],color=color,lw=.85,ls='--',
                marker='o',mfc='white',mew=.65,ms=2.5,markevery=20,label=f'{h} h，移动网格')
    ax.set(xlim=(0,1.24),ylim=(.04,.30),xlabel=r'物理半径 $r\,/\,\mathrm{cm}$',ylabel='水分浓度 / (kg/kg)')
    ax.xaxis.label.set_fontfamily('SimSun')
    ax.set_xticks([0,.3,.6,.9,1.2]);ax.legend(loc='lower left',fontsize=10)
    ax.text(.5,-.30,'(b) 完整径向剖面',transform=ax.transAxes,ha='center',fontsize=10)
    save_figure(fig,OUT/'q4_moving_mesh_validation');plt.close(fig)
    shutil.copy2(OUT/'q4_moving_mesh_validation.pdf',ROOT/'paper/cumcm-1.1.0/figures/q4_moving_mesh_validation.pdf')

    fig,axes=plt.subplots(1,2,figsize=(7.2,3.2))
    fig.subplots_adjust(left=.12,right=.98,bottom=.23,top=.90,wspace=.52)
    for ax,column,label,color in [(axes[0],5,'水分场最大绝对差 / (kg/kg)',CATEGORICAL[0]),
                                  (axes[1],6,'温度场最大绝对差 / °C',CATEGORICAL[1])]:
        ax.plot(hours,tr[:,column],lw=.6,color=color,rasterized=True)
        ax.set(xlim=(0,52),ylim=(0,None),xlabel='时间 / h',ylabel=label)
        if '$' in label:
            ax.yaxis.label.set_fontfamily('SimSun')
        ax.set_xticks([0,12,24,36,48]);ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    save_figure(fig,OUT/'q4_moving_mesh_errors');plt.close(fig)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--figures-only', action='store_true',
                        help='Render saved fields without rewriting numerical reports or tables')
    args = parser.parse_args()
    arrays=np.load(OUT/'fields.npz')
    render_figures(arrays)
    if args.figures_only:
        return
    report=json.loads((OUT/'summary.json').read_text(encoding='utf8'))
    report['event_comparison_note']='Own-event profiles and common mapping-event centre/surface values are distinguished; trajectories compare identical time levels.'
    (OUT/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    write_comparisons(arrays,report)
    rows=list(csv.DictReader((OUT/'comparison.csv').open(encoding='utf-8-sig')))
    labels={'drying_time':r'$t_d$/h'}
    for time,caption in [('6h','6 h'),('24h','24 h'),('48h','48 h'),('common_event',r'$t_d^{\rm map}$')]:
        for point,cn in [('center','中心'),('surface','动态表面')]:
            labels[f'{time}_{point}_moisture']=f'{caption}，{cn}'
    tex=[r'\begin{table}[H]',r'\centering',r'\caption{移动网格与固定域映射的数值比较}\label{tab:q4movingvalidation}',
         r'\begin{tabular}{lrrr}',r'\toprule',r'指标 & 固定域映射法 & 移动网格法 & 相对差\\',r'\midrule']
    md='| 指标 | 固定域映射法 | 移动网格法 | 相对差 |\n|---|---:|---:|---:|\n'
    for row in rows:
        if row['metric'] not in labels: continue
        a,b,d=map(float,[row['mapping'],row['moving_mesh'],row['relative_difference']])
        mant,exponent=f'{d:.2e}'.split('e')
        diff=rf'${mant}\times10^{{{int(exponent)}}}$' if d else '$0$'
        label=labels[row['metric']]
        tex.append(f'{label} & {a:.9f} & {b:.9f} & {diff}'+r'\\')
        md+=f'| {label} | {a:.12g} | {b:.12g} | {d:.3e} |\n'
    tex += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip',
            r'{\footnotesize 水分单位为 kg/kg；相对差以固定域结果为分母。末两行为同一固定域达标时刻的比较。}',r'\end{table}']
    (ROOT/'paper/cumcm-1.1.0/contents/sections/q4_moving_mesh_table.tex').write_text('\n'.join(tex)+'\n',encoding='utf8')
    (OUT/'comparison_table_zh.md').write_text(md,encoding='utf8')
    count=check_preservation(json.loads((OUT/'protected_files_sha256.json').read_text(encoding='utf8')))
    print(f'Figures and table generated; {count} original files unchanged.')


if __name__=='__main__':
    main()
