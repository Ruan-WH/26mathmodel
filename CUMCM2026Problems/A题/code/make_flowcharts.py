"""Export matching vector figures and editable draw.io flowcharts."""
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':['SimSun','Times New Roman'],'pdf.fonttype':42})


def chart(name,labels):
    target=ROOT/'drawio';target.mkdir(exist_ok=True)
    n=len(labels)
    fig,ax=plt.subplots(figsize=(7.0,n*.64));ax.set_xlim(0,10);ax.set_ylim(0,n)
    ax.axis('off')
    mx=ET.Element('mxfile',host='app.diagrams.net')
    dia=ET.SubElement(mx,'diagram',name=name)
    model=ET.SubElement(dia,'mxGraphModel');root=ET.SubElement(model,'root')
    ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0')
    for i,label in enumerate(labels):
        y=n-i-.5
        ax.add_patch(FancyBboxPatch((.4,y-.32),9.2,.64,boxstyle='round,pad=0.015',
                                  facecolor='#f4f7fa',edgecolor='#35546f',linewidth=.8))
        ax.text(5,y,label,ha='center',va='center',fontsize=10)
        if i<n-1:
            ax.annotate('',xy=(5,y-.65),xytext=(5,y-.34),arrowprops={'arrowstyle':'->','lw':.9})
        cell=ET.SubElement(root,'mxCell',id=str(i+2),value=label,
                           style='rounded=1;whiteSpace=wrap;html=0;fontSize=16;',vertex='1',parent='1')
        ET.SubElement(cell,'mxGeometry',x='40',y=str(i*100+30),width='650',height='65',attrib={'as':'geometry'})
        if i:
            edge=ET.SubElement(root,'mxCell',id='e'+str(i),edge='1',parent='1',source=str(i+1),target=str(i+2))
            ET.SubElement(edge,'mxGeometry',relative='1',attrib={'as':'geometry'})
    fig.savefig(target/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(target/(name+'.png'),bbox_inches='tight',dpi=200)
    plt.close(fig)
    ET.ElementTree(mx).write(target/(name+'.drawio'),encoding='utf-8',xml_declaration=True)


def main():
    chart('overall_roadmap',[
        '题给环境、半径数据与三组物性；统一单位与 PCHIP 插值',
        '问题一、二：固定半径热质扩散；逐秒求解与物理位置采样',
        '问题三：延长计算至全截面含水率达标；插值估计首达事件',
        '问题四：材料与网格同步收缩；同物性固定半径对照',
        '表面加密有限体积网格；Kirchhoff 水分通量；隐式非线性迭代',
        '空间、时间、质量平衡、解析模态及长期二维交叉核验',
        '统一生成结果、图表与论文；区分数值证据和物理模型局限'])
    chart('moving_boundary_solver',[
        '初值 T = 28 ℃、C = 2.55 kg/kg；初始化表面加密材料网格',
        '读取当前环境与 R(t)；径向位置 r = R(t) ξ',
        '材料速度等于网格速度；相对对流项为零',
        '更新热物性与界面扩散率；Picard 迭代至容差',
        '离散质量平衡核验；检查所有节点的最大含水率',
        '未达标则进入下一步；首次跨阈值则插值估计时间和剖面',
        '输出固定物理位置与动态表面；域外留空；记录核验数据'])


if __name__=='__main__':
    main()
