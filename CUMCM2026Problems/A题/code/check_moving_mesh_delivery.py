"""Check and package the Q4 validation without rerunning the integrator."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import shutil
import numpy as np
import pymupdf
from validate_moving_mesh import ROOT, OUT, check_preservation

protected=json.loads((OUT/'protected_files_sha256.json').read_text(encoding='utf8'))
count=check_preservation(protected)
a=np.load(OUT/'fields.npz');s=json.loads((OUT/'summary.json').read_text(encoding='utf8'))
assert a['mapping_moisture'].shape == (3051,161)
assert a['step_trace'].shape == (183001,8)
assert np.array_equal(np.diff(a['step_trace'][:,0]),np.ones(183000))
assert s['max_abs_center_moisture_difference']==float(a['step_trace'][:,7].max())
assert s['max_abs_temperature_field_difference']==float(a['step_trace'][:,6].max())
for k in ['mapping_moisture','moving_moisture','mapping_temperature','moving_temperature']:
    assert np.isfinite(a[k]).all()
paper=ROOT/'paper/cumcm-1.1.0'
log=(paper/'main.log').read_text(encoding='utf8',errors='replace')
bad=[x for x in ['Overfull','There were undefined references','Missing character:','Float too large'] if x in log]
assert not bad,bad
doc=pymupdf.open(paper/'main.pdf')
pages=[i+1 for i,page in enumerate(doc) if any(text in page.get_text() for text in
       ['移动网格独立验证','移动网格与固定域映射的数值比较','两种坐标实现的中心'])]
for i in pages:
    doc[i-1].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(OUT/f'paper_page_{i}.png')
shutil.copy2(paper/'main.pdf',ROOT/'A题_完整论文.pdf')
result=dict(protected_files_unchanged=count,pdf_pages=len(doc),validation_pages=pages,
            latex_overflow_or_missing_references=bad,minute_field_shape=list(a['mapping_moisture'].shape),
            per_second_trace_shape=list(a['step_trace'].shape),
            paper_sha256=hashlib.sha256((ROOT/'A题_完整论文.pdf').read_bytes()).hexdigest())
(OUT/'delivery_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
