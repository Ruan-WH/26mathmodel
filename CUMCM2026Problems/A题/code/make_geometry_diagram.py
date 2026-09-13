"""Build an editable DrawIO cylinder / cylindrical-coordinate schematic."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
doc=ET.Element('mxfile',host='app.diagrams.net')
diagram=ET.SubElement(doc,'diagram',name='药材几何与径向计算域',id='geometry')
model=ET.SubElement(diagram,'mxGraphModel',dx='1000',dy='720',grid='0',page='0',math='0',shadow='0')
tree=ET.SubElement(model,'root')
ET.SubElement(tree,'mxCell',id='0')
ET.SubElement(tree,'mxCell',id='1',parent='0')
count=1

def ident():
    global count
    count+=1
    return str(count)

def cell(x,y,w,h,style,value=''):
    el=ET.SubElement(tree,'mxCell',id=ident(),value=value,style=style,vertex='1',parent='1')
    ET.SubElement(el,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
    return el

def label(x,y,w,h,text,size=24,align='center'):
    html=f'<div style="font-family:Times New Roman;font-size:{size}px;color:#111111;">{text}</div>'
    return cell(x,y,w,h,f'text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;whiteSpace=wrap;fontSize={size};fontFamily=Times New Roman;',html)

def zh(s):return f'<span style="font-family:SimSun;">{s}</span>'
def ellipse(x,y,w,h,fill='none',dash=False,width=2.5,color='#111111'):
    return cell(x,y,w,h,f'ellipse;html=1;fillColor={fill};strokeColor={color};strokeWidth={width};dashed={int(dash)};')

def line(x1,y1,x2,y2,arrow='none',start='none',dash=False,color='#111111',width=2.5,points=None):
    el=ET.SubElement(tree,'mxCell',id=ident(),edge='1',parent='1',style=f'edgeStyle=none;html=1;rounded=0;strokeColor={color};strokeWidth={width};endArrow={arrow};startArrow={start};endFill=1;startFill=1;dashed={int(dash)};')
    g=ET.SubElement(el,'mxGeometry',relative='1',attrib={'as':'geometry'})
    ET.SubElement(g,'mxPoint',x=str(x1),y=str(y1),attrib={'as':'sourcePoint'})
    ET.SubElement(g,'mxPoint',x=str(x2),y=str(y2),attrib={'as':'targetPoint'})
    if points:
        arr=ET.SubElement(g,'Array',attrib={'as':'points'})
        for x,y in points: ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))

# Projection: the axial length is 625 units, transverse diameter 100 units,
# preserving L/(2 R0)=6.25 before oblique projection of the circular ends.
ellipse(753,150,44,100,fill='#F2F2F2')
cell(150,150,625,100,'fillColor=#F2F2F2;strokeColor=none;')
line(150,150,775,150);line(150,250,775,250)
ellipse(440.5,150,44,100,fill='#F2F2F2',dash=True,width=1.8,color='#666666')
ellipse(128,150,44,100,fill='#FFFFFF')

# Cartesian reference frame at the left-end centre, z along the cylinder axis.
line(150,200,860,200,arrow='block',dash=True,color='#666666',width=1.8)
line(150,200,91,254,arrow='block',width=2)
line(150,200,150,95,arrow='block',width=2)
label(94,185,25,30,'<i>O</i>')
label(74,247,25,30,'<i>x</i>')
label(133,64,34,30,'<i>y</i>')
label(860,183,30,30,'<i>z</i>')

# Initial radius and cylinder length.
line(150,200,150,150,arrow='classic',start='classic',width=2)
label(8,137,115,42,'<i>R</i><sub>0</sub> = 2 cm')
line(120,168,145,179,color='#666666',width=1.5)
line(150,265,150,312,color='#666666',width=1.5)
line(775,265,775,312,color='#666666',width=1.5)
line(150,301,775,301,arrow='classic',start='classic',width=2)
label(362.5,307,200,34,'<i>L</i> = 25 cm')
label(372.5,251,180,35,'<i>z</i> = <i>L</i>/2')

# Early-stage exchange directions (not universal sign assumptions).
line(344,105,344,143,arrow='block')
label(236.5,61,215,35,zh('预热热量传入'))
line(645,143,645,105,arrow='block')
label(550,61,190,35,zh('水分向外迁移'))
label(24,352,870,34,'(a) '+zh('初始圆柱几何与坐标系'))

# Enlarged midsection: the local origin is Om, not the end-centre O.
ellipse(124,454,192,192,fill='#F2F2F2')
line(220,550,355,550,arrow='block',width=2)
line(220,550,220,432,arrow='block',width=2)
label(355,535,30,30,'<i>x</i>');label(204,404,32,28,'<i>y</i>')
label(179,550,40,35,'<i>O</i><sub>m</sub>')
# A radial ray at 35 degrees, terminating on the circular boundary.
line(220,550,298.64,494.94,arrow='classic',width=2.5)
label(244,495,30,30,'<i>r</i>')
# Theta arc approximated by a short polyline, preserving editability.
import math
arc=[(220+40*math.cos(a),550-40*math.sin(a)) for a in [i*math.pi/180 for i in range(0,36,5)]]
line(*arc[0],*arc[-1],arrow='classic',width=1.8,points=arc[1:-1])
label(267,520,30,30,'<i>θ</i>')
label(78,658,284,35,zh('中截面放大：')+'<i>z</i> = <i>L</i>/2')

# The one-dimensional radial domain retains spatial gradients.
line(410,550,491,550,arrow='block',width=2.5)
label(379,492,144,38,zh('轴对称降维'))
line(565,550,820,550,width=3)
ellipse(559,544,12,12,fill='#111111',width=2)
ellipse(814,544,12,12,fill='#FFFFFF',width=2)
label(532,574,66,32,'<i>r</i> = 0')
label(759,574,122,32,'<i>r</i> = <i>R</i>(<i>t</i>)')
label(509,614,112,34,zh('中心对称'))
label(732.5,614,175,34,zh('表面对流交换'))
label(574,492,237,38,'<i>T</i>(<i>r</i>,<i>t</i>),  <i>C</i>(<i>r</i>,<i>t</i>)')
label(539.5,658,306,35,'0 ≤ <i>r</i> ≤ <i>R</i>(<i>t</i>)')
label(24,710,870,34,'(b) '+zh('中截面圆柱坐标与一维径向计算域'))

out=ROOT/'drawio/geometry_coordinates.drawio'
ET.ElementTree(doc).write(out,encoding='utf-8',xml_declaration=True)
print(out)
