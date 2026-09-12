# Academic Figure Skill Asset Confirmation (verified against assets/figures/)
# q1/q2 surfaces -> no continuous PDE surface asset -> cross-type inherit
# q2 map -> heatmap/plot_composition.py -> param inherit (continuous field, not counts)
# q3 threshold region -> no semantic match -> cross-type inherit
# q4 field / disks -> heatmap shared quantitative scale -> param inherit
# Baseline is copied below from the existing verified make_figures.py.
# Academic Figure Skill Typography Baseline — COPY VERBATIM, place at TOP of script
import matplotlib as mpl
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 8,
    "figure.titlesize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.6,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "legend.frameon": False,
})

mpl.rcParams.update({
    "font.family": ["Times New Roman", "SimSun"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold",
    "mathtext.sf": "Times New Roman",
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

# Academic Figure Skill Export Baseline — COPY VERBATIM
mpl.rcParams.update({
    "pdf.fonttype": 42,         # TrueType font embedding
    "svg.fonttype": "none",     # editable text in SVG
    "savefig.bbox": "tight",    # trim whitespace
    "savefig.dpi": 300,
})

def save_cns_figure(fig, filename):
    """Standard Academic Figure Skill export: vector PDF + 300dpi PNG preview."""
    fig.savefig(f"{filename}.pdf", bbox_inches="tight", dpi=300)
    fig.savefig(f"{filename}.png", bbox_inches="tight", dpi=300)




import json
import shutil
import sys
from pathlib import Path
import matplotlib.patheffects as pe
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Circle
from matplotlib import font_manager
sys.dont_write_bytecode = True
from solve_drying import property_q23

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
PAPER = ROOT / 'paper/cumcm-1.1.0/figures'
REPORT = ROOT / 'reports/figure_additions_20260911'
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
    save_cns_figure(fig,str(OUT/name))
    shutil.copy2(OUT/f'{name}.pdf',PAPER/f'{name}.pdf')
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
    ax.set_ylabel('半径 / cm',labelpad=6)
    ax.set_zlabel('')
    fig.text(.10,.62,zlabel,rotation=90,va='center',ha='center',fontsize=8)
    ax.view_init(elev=30,azim=45 if q=='q2' else -135)
    ax.set_box_aspect((1.7,1,1.05))
    for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:
        axis.pane.fill=False
        axis.pane.set_edgecolor('#DDDDDD')
        axis._axinfo['grid'].update(color='#E3E3E3',linewidth=.35)
    cb=fig.colorbar(mpl.cm.ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.82,.28,.022,.48]))
    cb.set_label(zlabel,labelpad=8)
    fig.text(.44,.03,'实线：中心边界    虚线：表面边界',ha='center',fontsize=8)
    METRICS[name]={'shape':list(v.shape),'min':float(v.min()),'max':float(v.max()),'time_range_s':[0,limit]}
    save(fig,name)

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
    labels=ax.clabel(cs,fmt='%g',fontsize=7,inline=True)
    for label in labels:
        label.set_path_effects([pe.withStroke(linewidth=1.4,foreground='#555555')])
    ax.plot(t,np.zeros_like(t),color='#222222',lw=.85)
    ax.plot(t,np.full_like(t,2),color='#222222',lw=.85,ls='--')
    ax.set(xlim=(t[0],t[-1]),ylim=(0,2),xlabel='时间 / '+('min' if q=='q1' else 'h'),ylabel='到药材中心的距离 / cm')
    ax.set_xticks([0,10,20,30] if q=='q1' else [0,1,2,3])
    ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.20,.023,.73]))
    cb.set_label(zlabel,labelpad=8)
    fig.text(.47,.035,'实线：中心    虚线：表面',ha='center',fontsize=8)
    METRICS[name]={'shape':list(v.shape),'min':float(v.min()),'max':float(v.max()),'time_range_s':[0,limit], 'plot':'2D heatmap with contour lines'}
    save(fig,name)

def diffusivity():
    d=read('q2'); m=d['times_s']<=10800
    t=d['times_s'][m]/3600; r=d['radius_m']*100
    z=property_q23(d['temperature_c'][m],d['moisture'][m])[-1]*1e9
    fig,ax=plt.subplots(figsize=(183/25.4,83/25.4))
    fig.subplots_adjust(left=.10,right=.84,bottom=.19,top=.92)
    im=ax.pcolormesh(t,r,z.T,cmap='viridis',shading='auto',rasterized=True)
    cs=ax.contour(t,r,z.T,levels=[6,8,10,12],colors='white',linewidths=.8)
    labels=ax.clabel(cs,fmt='%g',fontsize=8,inline=True)
    import matplotlib.patheffects as pe
    for label in labels:
        label.set_path_effects([pe.withStroke(linewidth=1.5,foreground='#555555')])
    ax.set(xlim=(0,3),ylim=(0,2),xlabel='时间 / h',ylabel='半径 / cm')
    ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.88,.19,.023,.73]))
    cb.set_label('扩散系数 D / (10⁻⁹ m²·s⁻¹)',labelpad=8)
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
    ax.text(14,.42,'未达标核心\nC > 0.15 kg/kg',ha='center',fontsize=10,color='#17466B')
    ax.text(43,1.55,'已达标外层\nC ≤ 0.15 kg/kg',ha='center',fontsize=10,
            bbox=dict(facecolor='white',edgecolor='none',alpha=.92,pad=4))
    ax.annotate(f'表面首达 {ts:.3f} h',xy=(ts,2),xytext=(ts+2,2.15),fontsize=8,
                arrowprops=dict(arrowstyle='-',color=GREY,lw=.7),annotation_clip=False)
    ax.annotate(f'中心首达 {t[-1]:.3f} h',xy=(t[-1],0),xytext=(42,.34),fontsize=8,
                arrowprops=dict(arrowstyle='->',color=ACCENT_RED,lw=.8))
    ax.set(xlim=(0,t[-1]),ylim=(0,2),xlabel='时间 / h',ylabel='半径 / cm')
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
    ax.clabel(con,fmt={.15:'0.15'},fontsize=8,inline=True)
    ax.text(27,1.73,'材料域外（留白）',ha='center',fontsize=9,color='#666666')
    ax.annotate('实时表面 R(t)',xy=(6,radii[np.argmin(abs(t-6))]),xytext=(10,1.75),
                arrowprops=dict(arrowstyle='->',color=BLACK,lw=.7),fontsize=8)
    ax.set(xlim=(0,t[-1]),ylim=(0,2.08),xlabel='时间 / h',ylabel='物理半径 / cm')
    ax.set_xticks([0,12,24,36,48]); ax.set_yticks([0,.5,1,1.5,2])
    cb=fig.colorbar(im,cax=fig.add_axes([.89,.48,.021,.46]));cb.set_label('水分浓度 / (kg·kg⁻¹)',labelpad=7)
    fig.text(.465,.38,'(a) 收缩材料域中的水分时空场',ha='center',fontsize=8)
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
        a.text(.5,1.07,f'{h:.2f} h' if j==5 else f'{h:g} h',transform=a.transAxes,ha='center',fontsize=8)
        a.text(.5,-.07,f'R = {rad:.3f} cm',transform=a.transAxes,ha='center',fontsize=7)
        details.append({'time_h':float(t[i]),'radius_cm':float(rad),'center_C':float(c[i,0])})
    fig.text(.50,.035,'(b) 等比例圆截面重建；虚线为初始外轮廓，共用上方水分色标',ha='center',fontsize=8)
    METRICS['q4_shrinking_field']={'snapshots':details,'all_time_samples':len(t),'method':'axisymmetric reconstruction of 1D radial solution, not independent 2D simulation'}
    save(fig,'q4_shrinking_field')

def main():
    sys.stdout.reconfigure(encoding='utf8')
    font_manager.findfont('Times New Roman',fallback_to_default=False)
    for chinese_font in ('SimSun','Songti SC','STSong'):
        try:
            font_manager.findfont(chinese_font,fallback_to_default=False)
        except ValueError:
            continue
        mpl.rcParams['font.family']=['Times New Roman',chinese_font]
        break
    else:
        raise RuntimeError('需要 SimSun、Songti SC 或 STSong 中至少一种中文字体')
    surface_heatmap('q1','temperature_c','q1_temperature_surface','温度 / °C','plasma',1800,[29,31,33,35,37])
    print('Q1 surface saved',flush=True)
    surface('q2','moisture','q2_moisture_surface','水分浓度 / (kg·kg⁻¹)',BLUE,10800,[1,1.5,2,2.55])
    print('Q2 surface saved',flush=True)
    diffusivity();threshold_front();shrinking()
    (REPORT/'metrics.json').write_text(json.dumps(METRICS,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(METRICS,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
