from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import pymupdf as fitz

audit = Path(__file__).parent
project = audit.parent.parent
paper = project / 'paper/cumcm-1.1.0'
root = project.parent.parent
def expand(path, base):
    text = re.sub(r'(?<!\\)%[^\n]*', '', path.read_text(encoding='utf-8-sig'))
    return re.sub(r'\\input\{([^}]+)\}',lambda m: expand(base / m[1],base),text)
source = expand(paper / 'main.tex',paper)
labels = re.findall(r'\\label\{([^}]+)\}',source)
refs = {key.strip() for group in re.findall(r'\\(?:[cC]?ref|eqref|pageref)\*?\{([^}]+)\}',source) for key in group.split(',')}
cites = {key.strip() for group in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}',source) for key in group.split(',')}
bib = set(re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',source))
protected = json.loads((audit.parent / 'page_limit_30_20260913/baseline_hashes.json').read_text(encoding='utf-8-sig'))
changed_protected = [name for name,digest in protected.items() if hashlib.sha256((root / name).read_bytes()).hexdigest()!=digest]
log = (paper / 'main.log').read_text(encoding='utf-8',errors='replace')
bad_log = [line for line in log.splitlines() if re.search(r'Overfull|(?:Reference|Citation).*undefined|There were undefined references|Missing character|Undefined control sequence|^!|Rerun to get cross-references',line)]

def body(base):
    return '\n'.join(expand(base / f'contents/sections/s{i}.tex',base) for i in range(1,11))
def float_content(text):
    items = {}
    for match in re.finditer(r'\\begin\{(figure|table)\}\[[^]]+\].*?\\end\{\1\}',text,re.S):
        label = re.search(r'\\label\{([^}]+)\}',match[0])[1]
        items[label] = re.sub(r'\s+',' ',re.sub(r'(\\begin\{(?:figure|table)\})\[[^]]+\]',r'\1',match[0])).strip()
    return items
old_floats = float_content(body(audit / 'before'))
new_floats = float_content(body(paper))
changed_floats = [label for label, content in old_floats.items() if new_floats.get(label)!=content]
layout = json.loads((audit / 'placement.json').read_text(encoding='utf-8'))
gaps = {item['label']:item['caption_page']-item['first_mention_page'] for item in layout['floats']}
old = fitz.open(audit / 'paper_before.pdf')
doc = fitz.open(paper / 'main.pdf')
def appendix(pdf):
    start = next(i for i,p in enumerate(pdf) if re.match(r'附录\s*A',p.get_text()))
    return [re.sub(r'\n\d+\s*$','',p.get_text()).strip() for p in list(pdf)[start:]]

checks = {
    'scope':'Figure/table placement and removal of repeated conclusions; no numerical recomputation.',
    'pre_appendix_pages':layout['pre_appendix_pages'],
    'appendix_A_page':layout['appendix_A_page'],'total_pages':len(doc),
    'figure_count':sum(label.startswith('fig:') for label in new_floats),
    'table_count':sum(label.startswith('tab:') for label in new_floats),
    'changed_figure_table_content_excluding_placement':changed_floats,
    'protected_file_count':len(protected),'changed_protected_files':changed_protected,
    'unresolved_references':sorted(refs-set(labels)),'unresolved_citations':sorted(cites-bib),
    'duplicate_labels':[k for k,v in Counter(labels).items() if v>1],
    'latex_errors_or_unresolved_or_overfull':bad_log,
    'max_first_mention_to_caption_page_gap':max(gaps.values()),
    'float_page_gaps':gaps,
    'remaining_repeated_conclusion_headings':source.count('本问结论与分析'),
    'appendix_text_unchanged':appendix(old)==appendix(doc),
    'pdf_sha256':hashlib.sha256((paper / 'main.pdf').read_bytes()).hexdigest(),
}
assert checks['pre_appendix_pages']==30 and checks['appendix_A_page']==31 and len(doc)==50, checks
assert not changed_floats and set(old_floats)==set(new_floats), checks
assert checks['figure_count']==14 and checks['table_count']==16, checks
assert not changed_protected and not bad_log and not checks['unresolved_references'] and not checks['unresolved_citations'] and not checks['duplicate_labels'], checks
assert checks['max_first_mention_to_caption_page_gap']<=1 and checks['remaining_repeated_conclusion_headings']==0 and checks['appendix_text_unchanged'], checks
(paper / 'main.txt').write_text('\f'.join(p.get_text() for p in doc),encoding='utf-8')
(audit / 'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
