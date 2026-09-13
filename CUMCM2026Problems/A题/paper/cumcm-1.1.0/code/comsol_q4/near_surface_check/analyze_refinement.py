# File: comsol_q4/near_surface_check/analyze_refinement.py
"""Read-only comparison of independent COMSOL runs against the saved FVM field."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from analyze_q4_comsol import read_comsol_wide,baseline_profile,comparison_times
ROOT=HERE.parents[1]
with np.load(ROOT/'results/q4/fields.npz') as z:base={k:z[k] for k in z.files}
event=json.loads((ROOT/'results/q4/summary.json').read_text(encoding='utf-8'))['drying_time_s']
target= comparison_times(event)
fields={};records=[]
for name,n,tol in json.loads((HERE/'manifest.json').read_text())['cases']:
 path=HERE/name/'q4_comsol_profiles.csv'
 if not path.exists():continue
 _,raw,times=read_comsol_wide(path)
 xi=raw[:,0]/.02;order=np.argsort(xi);xi=xi[order]
 tc=raw[order,2::4].T;c=raw[order,3::4].T
 indexes=[int(np.argmin(abs(times-t))) for t in target]
 selected=c[indexes];temp=tc[indexes]
 ref=np.array([np.interp(xi,base['xi'],baseline_profile(base,'moisture',t,event)) for t in target])
 tref=np.array([np.interp(xi,base['xi'],baseline_profile(base,'temperature_c',t,event)) for t in target])
 err=np.abs(selected-ref);i,j=np.unravel_index(np.argmax(err),err.shape)
 jcross=np.flatnonzero(c[:,0]<=.15)
 crossing=None
 if len(jcross):
  k=jcross[0];crossing=float((times[k-1]+(.15-c[k-1,0])/(c[k,0]-c[k-1,0])*(times[k]-times[k-1]))/3600)
 record={'case':name,'radial_elements':n or 'original_auto3','rtol':tol,
 'max_moisture_difference':float(err.max()),'at_time_h':float(target[i]/3600),'at_xi':float(xi[j]),
 'max_center_difference':float(err[:,0].max()),'max_surface_difference':float(err[:,-1].max()),
 'max_outer_10pct_difference':float(err[:,xi>=.9].max()),
 'max_temperature_difference':float(np.max(abs(temp-tref))),
 'center_C_at_FVM_event':float(selected[-1,0]),'surface_C_at_FVM_event':float(selected[-1,-1]),
 'estimated_COMSOL_event_h':crossing,'event_estimation_scope':'linear interpolation of saved output; not solver event detection',
 'per_time_max_difference':[float(v) for v in err.max(axis=1)]}
 fields[name]={'c':selected,'t':temp,'xi':xi}
 records.append(record)
 print(name,'max dC',record['max_moisture_difference'],'xi',record['at_xi'],'event',crossing,flush=True)
np.savez_compressed(HERE/'comparison_fields.npz',times_s=target,xi=xi,reference_moisture=ref,**{name+'_moisture':v['c'] for name,v in fields.items()})
comparisons=[]
for a,b in [('original_dense','original_tight'),('original_tight','graded80'),('graded80','graded160'),('graded160','graded320'),('graded320','graded320_tight')]:
 if a in fields and b in fields:
  comparisons.append({'a':a,'b':b,'max_moisture_difference':float(abs(fields[a]['c']-fields[b]['c']).max()),'max_temperature_difference':float(abs(fields[a]['t']-fields[b]['t']).max())})
with (HERE/'comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
manifest=json.loads((HERE/'manifest.json').read_text())
protected={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in manifest['source_sha256'].items()}
summary={'scope':'6 specified times and 1001 common reference radii; original input interpolation retained','cases':records,'successive_comparisons':comparisons,'protected_files_unchanged':protected}
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(comparisons,indent=2));print('protected',protected)
