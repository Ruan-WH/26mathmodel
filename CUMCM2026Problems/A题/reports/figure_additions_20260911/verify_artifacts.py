"""Verify preserved assets, new PDF embedding, references, and source provenance."""
import hashlib
import json
import re
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PAPER = ROOT / 'paper/cumcm-1.1.0'
before = json.loads((OUT/'original_figures_sha256.json').read_text(encoding='utf8'))
changed = [name for name,digest in before.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
assert not changed,changed
names=['q1_temperature_surface','q2_moisture_surface','q2_diffusivity_map','q3_drying_front','q4_shrinking_field']
fonts={}
for name in names:
    f=ROOT/'figures'/f'{name}.pdf'
    assert f.read_bytes()==(PAPER/'figures'/f.name).read_bytes()
    assert (ROOT/'figures'/f'{name}.png').stat().st_size>10000
    doc=pymupdf.open(f)
    fs=doc[0].get_fonts()
    assert any('SimSun' in font[3] for font in fs)
    assert any('TimesNewRoman' in font[3] for font in fs)
    for font in fs:
        assert len(doc.extract_font(font[0])[3])>0
    fonts[name]=[font[3] for font in fs]
aux=(PAPER/'main.aux').read_text(encoding='utf8')
pages={}
for key in ['q1surface','q2surface','q2diffusivity','q3front','q4field']:
    match=re.search(r'\\newlabel\{fig:'+key+r'\}\{\{(\d+)\}\{(\d+)\}',aux)
    assert match,key
    pages[key]={'figure':int(match[1]),'page':int(match[2])}
log=(PAPER/'main.log').read_text(encoding='utf8')
for error in ['There were undefined references','Overfull \\hbox','Overfull \\vbox','Missing character:','Float too large']:
    assert error not in log,error
doc=pymupdf.open(PAPER/'main.pdf')
body_end=None
for i,page in enumerate(doc):
    if '支撑材料文件列表' in page.get_text():
        body_end=i
        break
sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/'results'/q/'fields.npz' for q in ['q1','q2','q3','q4']]}
result={'original_asset_count':len(before),'changed_original_assets':changed,'new_figures':pages,'embedded_fonts':fonts,'total_pages':len(doc),'pages_before_appendices':body_end,'source_sha256':sources,'latex_blocking_issues':[]}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=True,indent=2))
