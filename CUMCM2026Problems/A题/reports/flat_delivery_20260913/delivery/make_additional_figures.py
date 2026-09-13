"""平铺支撑材料：主模型求解与主结果绘图。
环境：Python 3.11+，numpy、scipy、matplotlib；绘图需安装 Times New Roman
及 SimSun（宋体）字体。本交付副本无需外部输入Excel，附件1/2原始数值由同目录
input_data.py提供；数据来源和原始文件SHA-256写在该模块。
从解压根目录依次执行：
  python solve_drying.py --skip-convergence
  python run_q4_counterfactual.py
  python make_figures.py
  python make_additional_figures.py
第一个命令按原模型从初态计算四问；第二个命令生成第四问比较图所需的同物性固定半径
对照。计算可能耗时较长。--skip-convergence仅跳过主入口附带的时间步长与模型对照检查，
不改变主模型终算设置。运行后自动生成results/和figures/目录；ZIP本身没有目录。
图中的温湿场来自重新计算生成的NPZ，不能仅靠四个结果Excel替代全部内部场。
根目录result1.xlsx至result4.xlsx是原样保留的正式结果，本套命令不会改写这些文件。
这里只提供主模型和主结果图；COMSOL、独立验证图、论文排版与结果模板导出程序
不属于这个平铺包。canonical求解函数未改，只对输入读取和交付目录作适配。"""

# Academic Figure Skill Asset Confirmation (verified against assets/figures/)
# q1/q2 surfaces -> no continuous PDE surface asset -> cross-type inherit
# q2 map -> heatmap/plot_composition.py -> param inherit (continuous field, not counts)
# q3 threshold region -> no semantic match -> cross-type inherit
# q4 field / disks -> heatmap shared quantitative scale -> param inherit
# Shared CUMCM typography is applied after the common plot settings below.
import matplotlib as mpl
mpl.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})

# Academic Figure Skill Nature/Cell/Science Color Palette -- COPY VERBATIM
CATEGORICAL = ["#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666"]
CATEGORICAL_EXTENDED = [
    "#2166AC", "#B2182B", "#1B7837", "#F1A340", "#762A83", "#666666",
    "#4393C3", "#D6604D", "#5AAE61", "#B35806", "#9970AB", "#999999",
]
DIVERGING   = ["#2166AC", "#F7F7F7", "#B2182B"]
SEQUENTIAL  = ["#F7FBFF", "#6BAED6", "#08306B"]
ACCENT_RED  = "#B2182B"
GREY        = "#999999"
BLACK       = "#222222"

import json
import sys
from pathlib import Path
import matplotlib.patheffects as pe
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Circle
sys.dont_write_bytecode = True
from solve_drying import property_q23
from figure_style import configure_fonts, save_figure

configure_fonts()

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'figures'
REPORT = OUT
BLUE = LinearSegmentedColormap.from_list('moisture', SEQUENTIAL)
NORM_C = Normalize(0, 2.55)
METRICS = {}

def read(q):
    with np.load(ROOT / 'results' / q / 'fields.npz') as z:
        d = {k:z[k] for k in z.files}
    for key in ['temperature_c','moisture']:
        assert np.isfinite(d[key]).all()
        assert d[key].shape == (len(d['times_s']), len(d['xi'] if q == 'q4' else d['radius_m']))
    assert np.all(np.diff(d['times_s']) > 0)
    assert d['moisture'].min() >= 0
    assert np.max(np.diff(d['moisture'],axis=1)) < 2e-8
    return d

def summary(q):
    return json.loads((ROOT/'results'/q/'summary.json').read_text(encoding='utf8'))

def event_data(q):
    d=read(q); s=summary(q); end=s['drying_time_s']
    keep=d['times_s'] < end
    t=np.r_[d['times_s'][keep],end]/3600
    c=np.vstack([d['moisture'][keep],d['threshold_moisture']])
    assert abs(c[-1].max()-.15)<1e-9
    return d,s,t,c,keep

def save(fig,name):
    save_figure(fig,str(OUT/name))
    plt.close(fig)

def surface(q,key,name,zlabel,cmap,limit,ticks):
    d=read(q)
    mask=d['times_s']<=limit
    t=d['times_s'][mask]/(60 if q=='q1' else 3600)
    r=d['radius_m']*100
    v=d[key][mask]
    x,y=np.meshgrid(t,r,indexing='ij')
    fig=plt.figure(figsize=(183/25.4,108/25.4))
    ax=fig.add_axes([.04,.10,.76,.88],projection='3d')
    norm=Normalize(float(v.min()),float(v.max()))
    ax.plot_surface(x,y,v,cmap=cmap,norm=norm,rstride=1,cstride=1,
                    linewidth=0,antialiased=False,shade=False,rasterized=True)
    # Outline the two physical boundaries; all surface cells remain represented.
    ax.plot(t,np.zeros_like(t),v[:,0],color='#222222',lw=.9)
    ax.plot(t,np.full_like(t,2),v[:,-1],color='#222222',lw=.9,ls='--')
    ax.set(xlim=(t[0],t[-1]),ylim=(0,2),zlim=(ticks[0],ticks[-1]))
    ax.set_xticks([0,10,20,30] if q=='q1' else [0,1,2,3])
    ax.set_yticks([0,1,2]); ax.set_zticks(ticks)
    ax.set_xlabel('时间 / '+('min' if q=='q1' else 'h'),labelpad=7)
    ax.set_ylabel(r'半径 $r\,/\,\mathrm{cm}$',labelpad=6)
    ax.set_zlabel('')
    fig.text(.10,.62,zlabel,rotation=90,va='center',ha='center',fontsize=11)
    ax.view_init(elev=30,azim=45 if q=='q2' else -135)
    ax.set_box_aspect((1.7,1,1.05))
    for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:
        axis.pane.fill=False
        axis.pane.set_edgecolor('#DDDDDD')
        axis._axinfo['grid'].update(color='#E3E3E3',linewidth=.35)
    cb=fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.82,.28,.022,.48]))
    cb.set_label(zlabel,labelpad=8)
    fig.text(.44,.03,'实线：中心边界    虚线：表面边界',ha='center',fontsize=10)
    METRICS[name]={'shape':list(v.shape),'min':float(v.min()),'max':float(v.max()),'time_range_s':[0,limit]}
    save(fig,name)

def label_contours_inside(ax, contours):
    """Keep numeric labels inside the plotted domain after enlarging the type."""
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    points = []
    for segments in contours.allsegs:
        paths = [segment for segment in segments if len(segment) > 1]
        if not paths:
            continue
        vertices = np.concatenate(paths)
        normalized = (vertices - [xmin, ymin]) / [xmax - xmin, ymax - ymin]
        inside = ((normalized[:, 0] > .07) & (normalized[:, 0] < .96)
                  & (normalized[:, 1] > .10) & (normalized[:, 1] < .88))
        if not np.any(inside):
            continue
        candidates = vertices[inside]
        score = np.sum((normalized[inside] - [.55, .60]) ** 2, axis=1)
        points.append(tuple(candidates[np.argmin(score)]))
    return ax.clabel(contours, fmt='%g', fontsize=10, inline=True, manual=points)


def surface_heatmap(q,key,name,zlabel,cmap,limit,ticks):
    d=read(q)
    mask=d['times_s']<=limit
    t=d['times_s'][mask]/(60 if q=='q1' else 3600)
    r=d['radius_m']*100
    v=d[key][mask]
    fig,ax=plt.subplots(figsize=(183/25.4,82/25.4))
    fig.subplots_adjust(left=.10,right=.86,bottom=.20,top=.93)
    norm=Normalize(float(v.min()),float(v.max()))
    im=ax.pcolormesh(t,r,v.T,cmap=cmap,norm=norm,shading='auto',rasterized=True)
    cs=ax.contour(t,r,v.T,levels=ticks,colors='white',linewidths=.75)
    labels=label_contours_inside(ax,cs)
    for label in labels:
        label.set_color(BLACK)
        label.set_path_effects([pe.withStroke(linewidth=.8,foreground='white')])
    ax.plot(t,np.zeros_like(t),color='#222222',lw=.85)
    ax.plot(t,np.full_like(t,2),color='#222222',lw=.85,ls='--')
    ax.set(xlim=(t[0],t[-1]),ylim=(0,2),xlabel='时间 / '+('min' if q=='q1' else 'h'),ylabel=r'到药材中心的距离 $r\,/\,\mathrm{cm}$')
    ax.set_xticks([0,10,20,30] if q=='q1' else [0,1,2,3])
    ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.20,.023,.73]))
    cb.set_label(zlabel,labelpad=8)
    fig.text(.47,.035,'下边界：中心    上边界：表面',ha='center',fontsize=10)
    METRICS[name]={'shape':list(v.shape),'min':float(v.min()),'max':float(v.max()),'time_range_s':[0,limit], 'plot':'2D heatmap with contour lines'}
    save(fig,name)

def diffusivity():
    d=read('q2'); m=d['times_s']<=10800
    t=d['times_s'][m]/3600; r=d['radius_m']*100
    z=property_q23(d['temperature_c'][m],d['moisture'][m])[-1]*1e9
    fig,ax=plt.subplots(figsize=(183/25.4,78/25.4))
    fig.subplots_adjust(left=.10,right=.86,bottom=.20,top=.94)
    im=ax.pcolormesh(t,r,z.T,cmap='viridis',shading='auto',rasterized=True)
    cs=ax.contour(t,r,z.T,levels=[6,8,10,12],colors='white',linewidths=.8)
    labels=label_contours_inside(ax,cs)
    import matplotlib.patheffects as pe
    for label in labels:
        label.set_color(BLACK)
        label.set_path_effects([pe.withStroke(linewidth=.8,foreground='white')])
    ax.set(xlim=(0,3),ylim=(0,2),xlabel='时间 / h',ylabel=r'到药材中心的距离 $r\,/\,\mathrm{cm}$')
    ax.plot(t,np.zeros_like(t),color='#222222',lw=.8)
    ax.plot(t,np.full_like(t,2),color='#222222',lw=.8,ls='--')
    ax.set_xticks([0,1,2,3])
    ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.20,.023,.74]))
    cb.set_label(r'扩散系数 $D\,/\,(10^{-9}\,\mathrm{m^2/s})$',labelpad=8)
    METRICS['q2_diffusivity_map']={'shape':list(z.shape),'min_1e9':float(z.min()),'max_1e9':float(z.max()),'center_end_1e9':float(z[-1,0]),'surface_end_1e9':float(z[-1,-1])}
    save(fig,'q2_diffusivity_map')

def threshold_front():
    d,s,t,c,keep=event_data('q3'); r=d['radius_m']*100
    front=np.empty(len(t))
    for i,row in enumerate(c):
        if row[-1]>.15: front[i]=2
        elif row[0]<=.15+1e-12: front[i]=0
        else: front[i]=np.interp(.15,row[::-1],r[::-1])
    fig,ax=plt.subplots(figsize=(183/25.4,85/25.4))
    fig.subplots_adjust(left=.10,right=.97,bottom=.19,top=.90)
    ax.fill_between(t,0,front,facecolor='#BFD7EA',edgecolor='none')
    ax.fill_between(t,front,2,facecolor='#F5F5F5',edgecolor='#D2D2D2',hatch='///',linewidth=0)
    start=np.argmax(c[:,-1]<=.15)
    ts=np.interp(.15,c[start-1:start+1,-1][::-1],t[start-1:start+1][::-1])
    ax.plot(t[start:],front[start:],color=ACCENT_RED,lw=1.8)
    ax.scatter([ts,t[-1]],[2,0],s=24,color=ACCENT_RED,zorder=6,clip_on=False)
    ax.text(14,.42,'未达标区域\n'+r'$C > 0.15\ \mathrm{kg/kg}$',ha='center',fontsize=10,color='#17466B')
    ax.text(43,1.55,'已达标区域\n'+r'$C < 0.15\ \mathrm{kg/kg}$',ha='center',fontsize=10,
            bbox=dict(facecolor='white',edgecolor='none',alpha=.92,pad=3))
    ax.annotate(f'表面首达 {ts:.3f} h',xy=(ts,2),xytext=(ts+2,2.13),fontsize=10,
                arrowprops=dict(arrowstyle='-',color=GREY,lw=.7),annotation_clip=False)
    ax.annotate(f'中心首达 {t[-1]:.3f} h',xy=(t[-1],0),xytext=(40,.32),fontsize=10,
                arrowprops=dict(arrowstyle='->',color=ACCENT_RED,lw=.8))
    ax.set(xlim=(0,t[-1]),ylim=(0,2),xlabel='时间 / h',ylabel=r'半径 $r\,/\,\mathrm{cm}$')
    event_h = float(s["drying_time_h"])
    ticks = [0, 12, 24, 36, 48, event_h]
    ax.set_xticks(ticks); ax.set_xticklabels(['0', '12', '24', '36', '48', f'{event_h:.3f}'])
    ax.set_yticks([0,.5,1,1.5,2])
    METRICS['q3_drying_front']={'surface_crossing_h':float(ts),'center_crossing_h':float(t[-1]),'lag_h':float(t[-1]-ts),'radial_interpolation':'linear between 21 saved output nodes','time_samples':len(t)}
    np.savez_compressed(REPORT/'q3_front_data.npz',time_h=t,threshold_radius_cm=front)
    save(fig,'q3_drying_front')

def shrinking():
    d,s,t,c,keep=event_data('q4')
    radii=np.r_[d['radii_m'][keep]*100,s['radius_at_end_cm']]
    xi=d['xi']; xx=np.broadcast_to(t[:,None],c.shape); yy=radii[:,None]*xi
    fig=plt.figure(figsize=(183/25.4,139/25.4))
    ax=fig.add_axes([.095,.48,.74,.46])
    im=ax.pcolormesh(xx,yy,c,cmap=BLUE,norm=NORM_C,shading='gouraud',rasterized=True)
    ax.plot(t,radii,color=BLACK,lw=1.2)
    con=ax.contour(xx,yy,c,levels=[.15],colors=ACCENT_RED,linewidths=1.2)
    # Place the label on the middle of the threshold curve, away from the axes.
    label_index=int(np.argmin(abs(t-.60*t[-1])))
    label_radius=float(np.interp(.15,c[label_index,::-1],yy[label_index,::-1]))
    contour_labels = ax.clabel(con,fmt={.15:r'$C = 0.15$'},fontsize=10,inline=True,
                              manual=[(float(t[label_index]),label_radius)])
    for label in contour_labels:
        label.set_color(BLACK)
        label.set_fontweight('normal')
        label.set_path_effects([pe.withStroke(linewidth=.8,foreground='white')])
    ax.text(32,1.73,'材料域外（留白）',ha='center',fontsize=10,color='#666666')
    ax.annotate(r'实时表面 $R(t)$',xy=(6,radii[np.argmin(abs(t-6))]),xytext=(8,1.75),
                arrowprops=dict(arrowstyle='->',color=BLACK,lw=.7),fontsize=10)
    ax.set(xlim=(0,t[-1]),ylim=(0,2.08),xlabel='时间 / h',ylabel=r'物理半径 $r\,/\,\mathrm{cm}$')
    ax.set_xticks([0,12,24,36,48]); ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.48,.021,.46]));cb.set_label(r'水分浓度 $C\,/\,(\mathrm{kg/kg})$',labelpad=7)
    fig.text(.465,.38,'(a) 收缩材料域中的水分时空场',ha='center',fontsize=10)
    requested=[0,6,12,24,36,float(t[-1])]
    theta=np.linspace(0,2*np.pi,181)
    details=[]
    for j,h in enumerate(requested):
        i=int(np.argmin(abs(t-h))); rad=radii[i]
        a=fig.add_axes([.035+j*.16,.08,.145,.25])
        rr,tt=np.meshgrid(xi*rad,theta)
        zz=np.broadcast_to(c[i],rr.shape)
        a.pcolormesh(rr*np.cos(tt),rr*np.sin(tt),zz,cmap=BLUE,norm=NORM_C,shading='gouraud',rasterized=True)
        a.add_patch(Circle((0,0),rad,fill=False,ec=BLACK,lw=.65))
        a.add_patch(Circle((0,0),2,fill=False,ec='#BBBBBB',lw=.55,ls='--'))
        a.set(xlim=(-2.15,2.15),ylim=(-2.15,2.15),aspect='equal');a.axis('off')
        a.text(.5,1.07,f'{h:.2f} h' if j==5 else f'{h:g} h',transform=a.transAxes,ha='center',fontsize=10)
        a.text(.5,-.07,rf'$R = {rad:.3f}$ cm',transform=a.transAxes,ha='center',fontsize=10)
        details.append({'time_h':float(t[i]),'radius_cm':float(rad),'center_C':float(c[i,0])})
    fig.text(.50,.025,'(b) 等比例圆截面重建；虚线为初始外轮廓，共用上方水分色标',ha='center',fontsize=10)
    METRICS['q4_shrinking_field']={'snapshots':details,'all_time_samples':len(t),'method':'axisymmetric reconstruction of 1D radial solution, not independent 2D simulation'}
    save(fig,'q4_shrinking_field')

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sys.stdout.reconfigure(encoding='utf8')
    surface_heatmap('q1','temperature_c','q1_temperature_surface','温度 / °C','plasma',1800,[29,31,33,35,37])
    print('Q1 surface saved',flush=True)
    surface_heatmap('q2','moisture','q2_moisture_surface',r'水分浓度 $C\,/\,(\mathrm{kg/kg})$',BLUE,10800,[1,1.5,2,2.5])
    print('Q2 surface saved',flush=True)
    diffusivity();threshold_front();shrinking()
    (REPORT/'metrics.json').write_text(json.dumps(METRICS,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(METRICS,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
