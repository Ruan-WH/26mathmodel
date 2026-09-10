from pathlib import Path
import sys,json,time
import numpy as np
sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
root=next(Path('D:/26mathmodel/CUMCM2026Problems').glob('A*'))
sys.path.insert(0,str(root/'code'))
import solve_drying as m
env=m.load_environment();rh=m.load_radius_history();out=Path(__file__).parent
records=[]
for nodes in [21,41,81]:
    m.NODES=nodes
    entry={'nodes':nodes,'cases':{}}
    for q in [1,2,3,4]:
        if q==4: sim=m.simulate_moving(env,rh,dt_s=10,output_interval_s=60)
        else: sim=m.simulate_fixed(env,m.property_q1 if q==1 else m.property_q23,
            end_time_s={1:1800,2:10800,3:None}[q],dt_s=1 if q<=2 else 10,
            output_interval_s=60,stop_at_threshold=q==3)
        item={'threshold_h':float(sim['threshold_time_s'])/3600 if q>=3 else None,
              'last_s':float(sim['last_time_s']),
              'end_temperature_center_surface':[float(sim['temperature_c'][-1,0]),float(sim['temperature_c'][-1,-1])],
              'end_moisture_center_surface':[float(sim['moisture'][-1,0]),float(sim['moisture'][-1,-1])],
              'sample_end_moisture':sim['moisture'][-1,::(nodes-1)//20].tolist(),
              'sample_end_temperature':sim['temperature_c'][-1,::(nodes-1)//20].tolist()}
        if q>=3:item['threshold_moisture']=sim['threshold_moisture'][::(nodes-1)//20].tolist()
        if q==3:
            with np.load(root/'results/q2/fields.npz') as q2:
                t=sim['times_s']; mask=t<=10800; idx=t[mask].astype(int)
                item['q2_first3h_max_moisture_difference']=float(np.max(np.abs(sim['moisture'][mask,::(nodes-1)//20]-q2['moisture'][idx])))
        entry['cases'][f'q{q}']=item
        print(nodes,f'q{q}',json.dumps(item),flush=True)
    records.append(entry)
    (out/'grid_results.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
