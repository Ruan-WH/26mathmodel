from pathlib import Path
import hashlib
import json
import re
from collections import Counter

import pymupdf
from PIL import Image, ImageDraw

ROOT = Path('D:/26mathmodel')
PROJECT = ROOT / 'CUMCM2026Problems/A题'
PAPER = PROJECT / 'paper/cumcm-1.1.0'
AUDIT = PROJECT / 'reports/page_limit_30_20260913'
PREVIEW = AUDIT / 'preview'
PREVIEW.mkdir(exist_ok=True)

def expand(path):
    raw = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text(encoding='utf-8-sig'))
    return re.sub(r'\\input\{([^}]+)\}', lambda m: expand(PAPER / m[1]), raw)

src = expand(PAPER / 'main.tex')
labels = re.findall(r'\\label\{([^}]+)\}', src)
refs = {key.strip() for group in re.findall(r'\\(?:[cC]?ref|eqref|pageref)\*?\{([^}]+)\}', src) for key in group.split(',')}
cites = {key.strip() for group in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}', src) for key in group.split(',')}
bib = set(re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}', src))
hashes = json.loads((AUDIT / 'baseline_hashes.json').read_text(encoding='utf-8-sig'))
changed_protected = [name for name, digest in hashes.items() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
log = (PAPER / 'main.log').read_text(encoding='utf-8', errors='replace')
bad_log = [line for line in log.splitlines() if re.search(r'Overfull|(?:Reference|Citation).*undefined|There were undefined references|Missing character|Undefined control sequence|^!|Rerun to get cross-references', line)]

old = pymupdf.open(AUDIT / 'paper_before.pdf')
doc = pymupdf.open(PAPER / 'main.pdf')
def appendix_start(pdf):
    return next(i + 1 for i, page in enumerate(pdf) if re.match(r'附录\s*A', page.get_text()))
before_start, after_start = appendix_start(old), appendix_start(doc)
def body_floats(pdf, limit, kind):
    return sorted({int(m) for p in list(pdf)[:limit] for m in re.findall(r'^' + kind + r'\s*(\d+)\s', p.get_text(), re.M)})
def appendix_text(pdf, start):
    return [re.sub(r'\n\d+\s*$', '', p.get_text()).strip() for p in list(pdf)[start-1:]]

checks = {
    'scope': 'Paper shortening and layout only; no numerical solver rerun.',
    'before_total_pages': len(old), 'after_total_pages': len(doc),
    'before_pre_appendix_pages': before_start - 1, 'after_pre_appendix_pages': after_start - 1,
    'before_appendix_A_page': before_start, 'after_appendix_A_page': after_start,
    'protected_file_count': len(hashes), 'changed_protected_files': changed_protected,
    'unresolved_references': sorted(refs-set(labels)), 'unresolved_citations': sorted(cites-bib),
    'duplicate_labels': [k for k,v in Counter(labels).items() if v>1],
    'latex_error_overfull_or_unresolved_messages': bad_log,
    'figure_numbers_before': body_floats(old, before_start - 1, '图'),
    'figure_numbers_after': body_floats(doc, after_start - 1, '图'),
    'table_numbers_before': body_floats(old, before_start - 1, '表'),
    'table_numbers_after': body_floats(doc, after_start - 1, '表'),
    'appendix_text_unchanged_except_page_numbers': appendix_text(old, before_start) == appendix_text(doc, after_start),
    'pdf_sha256': hashlib.sha256((PAPER / 'main.pdf').read_bytes()).hexdigest(),
}
assert after_start == 31 and len(doc) == 50, checks
assert not changed_protected and not bad_log and not checks['unresolved_references'] and not checks['unresolved_citations'] and not checks['duplicate_labels'], checks
assert checks['figure_numbers_before'] == checks['figure_numbers_after'] == list(range(1,15)), checks
assert checks['table_numbers_before'] == checks['table_numbers_after'] == list(range(1,17)), checks
assert checks['appendix_text_unchanged_except_page_numbers'], checks
(PAPER / 'main.txt').write_text('\f'.join(p.get_text() for p in doc), encoding='utf-8')
(AUDIT / 'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')

for group in range(5):
    canvas = Image.new('RGB', (1230, 1190), '#dedede')
    draw = ImageDraw.Draw(canvas)
    for j in range(6):
        index = group*6+j
        pix = doc[index].get_pixmap(matrix=pymupdf.Matrix(0.66,0.66), alpha=False)
        im = Image.frombytes('RGB', [pix.width,pix.height], pix.samples)
        x, y = (j%3)*410+8, (j//3)*595+26
        canvas.paste(im, (x,y))
        draw.text((x,y-18), f'Page {index+1}', fill='black')
    canvas.save(PREVIEW / f'contact_{group+1}.png')
for number in [6,9,10,13,14,17,18,22,23,24,27,28,29,30,31]:
    doc[number-1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5), alpha=False).save(PREVIEW / f'page_{number:02d}.png')
print(json.dumps(checks, ensure_ascii=False, indent=2))
