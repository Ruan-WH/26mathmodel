from pathlib import Path
import hashlib
import json
import re
import statistics

import pymupdf
from PIL import Image, ImageDraw

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
PAPER = PROJECT / 'paper/cumcm-1.1.0'
OUT = PROJECT.parents[1] / 'tmp/pdf_appendix_preview'
OUT.mkdir(parents=True, exist_ok=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


manifest = json.loads((AUDIT / 'source_manifest.json').read_text(encoding='utf-8'))
source_checks = []
for item in manifest:
    raw = (PROJECT / item['source']).read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    copied = (PAPER / item['appendix_copy']).read_text(encoding='utf-8')
    assert sha(raw) == item['source_sha256']
    assert copied.split('\n', 1) == [item['first_line'], text]
    compile(copied, item['source'], 'exec')
    source_checks.append({'file': item['source'], 'source_lines': item['source_lines'],
                          'filename_comment_correct': True, 'full_source_identical': True,
                          'python_syntax_pass': True})

doc = pymupdf.open(PAPER / 'main.pdf')
baseline_pdf = AUDIT / 'paper_before.pdf'
before = pymupdf.open(baseline_pdf) if baseline_pdf.exists() else None
saved_checks_path = AUDIT / 'appendix_checks.json'
saved_checks = json.loads(saved_checks_path.read_text(encoding='utf-8')) if saved_checks_path.exists() else {}
texts = [page.get_text() for page in doc]
if before is not None:
    assert all(texts[i] == before[i].get_text() for i in range(30))
body_pixels = []
for i in range(30):
    actual = doc[i].get_pixmap(matrix=pymupdf.Matrix(1, 1)).samples
    expected_hash = (sha(before[i].get_pixmap(matrix=pymupdf.Matrix(1, 1)).samples)
                     if before is not None else saved_checks['body_pixel_checks'][i]['render_sha256'])
    assert sha(actual) == expected_hash, f'Body page {i+1} changed visually'
    body_pixels.append({'page': i + 1, 'render_sha256': sha(actual), 'unchanged': True})
assert texts[30].startswith('附录A')
assert texts[31].startswith('附录B')
assert '.drawio' not in texts[30] and '.md' not in texts[30]
assert 'AI工具使用详情.pdf' in re.sub(r'\s+', '', texts[30])

aux = (PAPER / 'main.aux').read_text(encoding='utf-8')
starts = []
for i, item in enumerate(manifest, 1):
    match = re.search(r'\\newlabel\{app:source' + str(i) + r'\}\{\{.*?\}\{(\d+)\}', aux)
    assert match, item['source']
    page = int(match.group(1))
    assert re.sub(r'\s+', '', item['first_line']) in re.sub(r'\s+', '', texts[page-1])
    starts.append(page)
    source_checks[i-1]['pdf_first_page'] = page
for i, item in enumerate(source_checks):
    match = re.search(r'\\newlabel\{app:source' + str(i+1) + r'end\}\{\{.*?\}\{(\d+)\}', aux)
    assert match
    item['pdf_last_page'] = int(match.group(1))

# Validate centering from rendered PDF text coordinates, not only LaTeX column settings.
page = doc[30]
rules = sorted([d['rect'] for d in page.get_drawings() if d['rect'].width > 400], key=lambda r: r.y0)
assert len(rules) == 3
left, right = rules[0].x0, rules[0].x1
tab_padding = 10 * 72 / 72.27
textwidth = (right - left - 2 * tab_padding) / 0.93
first_width = 0.48 * textwidth + tab_padding
expected_centers = [left + first_width/2, left + first_width + (right-left-first_width)/2]
data_lines = []
for block in page.get_text('dict')['blocks']:
    for line in block.get('lines', []):
        x0, y0, x1, y1 = line['bbox']
        if y0 <= rules[1].y0 or y1 >= rules[2].y0:
            continue
        center = (x0+x1)/2
        column = 0 if center < left+first_width else 1
        error = center-expected_centers[column]
        data_lines.append({'text': ''.join(s['text'] for s in line['spans']),
                           'column': column+1, 'center_pt': center,
                           'expected_center_pt': expected_centers[column],
                           'error_pt': error})
assert len(data_lines) >= 24
# Proportional Chinese punctuation uses optical side bearing; 3 pt is below one small glyph.
assert max(abs(line['error_pt']) for line in data_lines) < 3

log = (PAPER/'main.log').read_text(encoding='utf-8', errors='replace')
bad_patterns = [r'^!', 'Missing character:', r'Overfull \\hbox',
                r'Overfull \\vbox', 'Undefined control sequence',
                'There were undefined references', 'multiply defined',
                r'Label\(s\) may have changed']
bad = [p for p in bad_patterns if re.search(p, log, flags=re.M)]
assert not bad, bad
assert 'Output written on main.pdf' in log

overflow = []
for i in range(30, len(doc)):
    for block in doc[i].get_text('dict')['blocks']:
        for line in block.get('lines', []):
            if line['bbox'][0] < 65 or line['bbox'][2] > doc[i].rect.width-65:
                overflow.append({'page': i+1, 'bbox': line['bbox'],
                                 'text': ''.join(s['text'] for s in line['spans'])})
    doc[i].get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(OUT/f'page_{i+1:03d}.png')
assert not overflow, overflow[:5]

for sheet_start in range(30, len(doc), 12):
    sheet = Image.new('RGB', (1160, 1260), '#dddddd')
    draw = ImageDraw.Draw(sheet)
    for j, i in enumerate(range(sheet_start, min(sheet_start+12, len(doc)))):
        with Image.open(OUT/f'page_{i+1:03d}.png') as im:
            im.thumbnail((280, 396))
            x, y = (j % 4)*290+5, (j//4)*420+20
            sheet.paste(im, (x, y))
            draw.text((x, y-16), f'Page {i+1}', fill='black')
    sheet.save(OUT/f'contact_{sheet_start+1:03d}.png')

(PAPER/'main.txt').write_text('\n\f\n'.join(texts), encoding='utf-8')
report = {'status': 'PASS', 'pdf_pages': len(doc), 'body_pages': 30,
          'appendix_A_page': 31, 'appendix_B_page': 32,
          'source_file_count': len(manifest),
          'original_source_lines': sum(i['source_lines'] for i in manifest),
          'source_checks': source_checks, 'body_pixel_checks': body_pixels,
          'appendix_A_data_centering_max_abs_error_pt': max(abs(i['error_pt']) for i in data_lines),
          'appendix_A_centering_details': data_lines,
          'appendix_A_vertical_alignment': 'm columns; visually reviewed',
          'no_latex_errors_missing_glyphs_or_overfull_boxes': True,
          'all_appendix_pages_rendered': True,
          'pdf_sha256': sha((PAPER/'main.pdf').read_bytes())}
(AUDIT/'appendix_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['source_checks', 'body_pixel_checks', 'appendix_A_centering_details']}, ensure_ascii=False, indent=2))
