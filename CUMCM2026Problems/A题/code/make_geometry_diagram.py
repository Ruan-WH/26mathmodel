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

def label(x,y,w,h,text,size=24):
    html=f'<div style="font-family:Times New Roman;font-size:{size}px;color:#111111;">{text}</div>'
    return cell(x,y,w,h,f'text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize={size};fontFamily=Times New Roman;',html)

def zh(s):return f'<span style="font-family:SimSun;">{s}</span>'
def ellipse(x,y,w,h,fill='none',dash=False,width=2.5):
    return cell(x,y,w,h,f'ellipse;html=1;fillColor={fill};strokeColor=#111111;strokeWidth={width};dashed={int(dash)};')

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
ellipse(753,130,44,100,fill='#F2F2F2')
cell(150,130,625,100,'fillColor=#F2F2F2;strokeColor=none;')
line(150,130,775,130);line(150,230,775,230)
ellipse(440.5,130,44,100,fill='#FFFFFF',dash=True,width=2)
ellipse(128,130,44,100,fill='#FFFFFF')

# Cartesian reference frame at the left-end centre, z along the cylinder axis.
line(150,180,860,180,arrow='block',dash=True,width=2)
line(150,180,87,235,arrow='block',width=2)
line(150,180,150,62,arrow='block',width=2)
label(111,179,25,30,'<i>O</i>')
label(71,226,25,30,'<i>x</i>')
label(133,30,34,30,'<i>y</i>')
label(860,163,30,30,'<i>z</i>')

# Initial radius and cylinder length.
line(150,180,150,130,arrow='classic',start='classic',width=2)
label(8,110,115,62,'<i>R</i><sub>0</sub> = 2 cm')
line(120,143,145,155,color='#666666',width=1.5)
line(150,244,150,292,color='#666666',width=1.5)
line(775,244,775,292,color='#666666',width=1.5)
line(150,278,775,278,arrow='classic',start='classic',width=2)
label(365,284,200,34,'<i>L</i> = 25 cm')
label(403,232,180,35,'<i>z</i> = <i>L</i>/2')

# Early-stage exchange directions (not universal sign assumptions).
line(344,66,344,120,arrow='block')
label(235,24,215,35,zh('预热热量传入'))
line(645,121,645,67,arrow='block')
label(555,24,190,35,zh('水分向外迁移'))
label(310,323,340,32,'(a) '+zh('初始圆柱几何与坐标系'))

# Enlarged midsection: the local origin is Om, not the end-centre O.
ellipse(144,407,206,206,fill='#F2F2F2')
line(247,510,386,510,arrow='block',width=2)
line(247,510,247,377,arrow='block',width=2)
label(385,499,30,30,'<i>x</i>');label(232,346,30,30,'<i>y</i>')
label(207,508,40,35,'<i>O</i><sub>m</sub>')
# A radial ray at 35 degrees, terminating on the circular boundary.
line(247,510,331.37,450.92,arrow='classic',width=2.5)
label(273,453,30,30,'<i>r</i>')
# Theta arc approximated by a short polyline, preserving editability.
import math
arc=[(247+42*math.cos(a),510-42*math.sin(a)) for a in [i*math.pi/180 for i in range(0,36,5)]]
line(*arc[0],*arc[-1],arrow='classic',width=1.8,points=arc[1:-1])
label(294,480,30,30,'<i>θ</i>')
label(125,622,245,35,zh('中截面放大：')+'<i>z</i> = <i>L</i>/2')

# The one-dimensional radial domain retains spatial gradients.
line(425,511,509,511,arrow='block',width=2.5)
label(411,443,128,48,zh('轴对称降维'))
line(554,510,833,510,width=3)
ellipse(548,504,12,12,fill='#111111',width=2)
ellipse(827,504,12,12,fill='#FFFFFF',width=2)
label(521,536,66,32,'<i>r</i> = 0')
label(773,536,122,32,'<i>r</i> = <i>R</i>(<i>t</i>)')
label(528,577,112,34,zh('中心对称'))
label(747,577,175,34,zh('表面对流交换'))
label(582,447,237,38,'<i>T</i>(<i>r</i>,<i>t</i>),  <i>C</i>(<i>r</i>,<i>t</i>)')
label(546,623,306,35,'0 ≤ <i>r</i> ≤ <i>R</i>(<i>t</i>)')
label(188,680,608,34,'(b) '+zh('中截面圆柱坐标与一维径向计算域'))

out=ROOT/'drawio/geometry_coordinates.drawio'
ET.ElementTree(doc).write(out,encoding='utf-8',xml_declaration=True)
print(out)
