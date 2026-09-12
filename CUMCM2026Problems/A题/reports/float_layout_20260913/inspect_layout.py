from pathlib import Path
import json
import re
import pymupdf as fitz
from PIL import Image, ImageDraw

audit = Path(__file__).parent
paper = audit.parent.parent / 'paper/cumcm-1.1.0'
preview = audit / 'preview'
preview.mkdir(exist_ok=True)
doc = fitz.open(paper / 'main.pdf')
start = next(i+1 for i,p in enumerate(doc) if re.match(r'附录\s*A',p.get_text()))
aux = (paper / 'main.aux').read_text(encoding='utf-8')
floats = []
for label, number, page in re.findall(r'\\newlabel\{((?:fig|tab):[^}]+)\}\{\{([^}]+)\}\{(\d+)\}',aux):
    kind = '图' if label.startswith('fig:') else '表'
    occurrences = [i+1 for i,p in enumerate(doc[:start-1]) if re.search(kind+re.escape(number)+r'(?!\d)', re.sub(r'\s+','',p.get_text()))]
    floats.append({'label':label,'number':kind+number,'caption_page':int(page),'first_mention_page':min(occurrences) if occurrences else None,'mention_pages':occurrences})

(audit / 'placement.json').write_text(json.dumps({'total_pages':len(doc),'pre_appendix_pages':start-1,'appendix_A_page':start,'floats':floats},ensure_ascii=False,indent=2),encoding='utf-8')
for offset in range(0,start-1,6):
    canvas=Image.new('RGB',(1230,1190),'#dedede')
    draw=ImageDraw.Draw(canvas)
    for j in range(min(6,start-1-offset)):
        index=offset+j
        pix=doc[index].get_pixmap(matrix=fitz.Matrix(.66,.66),alpha=False)
        im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
        x,y=(j%3)*410+8,(j//3)*595+26
        canvas.paste(im,(x,y)); draw.text((x,y-18),f'Page {index+1}',fill='black')
    canvas.save(preview/f'contact_{offset//6+1}.png')
for i,p in enumerate(doc[:start]):
    p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(preview/f'page_{i+1:02d}.png')
print('Total',len(doc),'pre-appendix',start-1,'appendix A',start)
for item in floats: print(item['label'],item['first_mention_page'],'->',item['caption_page'])
for i,p in enumerate(doc[:start]):
    text=p.get_text().replace('\n',' ')
    print(i+1,text[:50],'|',text[-70:])
