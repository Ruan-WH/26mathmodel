"""Independent spatial/time refinement checks; does not overwrite production fields."""
from pathlib import Path
import json
import sys
import numpy as np
import solve_drying as model


def run():
    environment=model.load_environment(); radius=model.load_radius_history()
    saved_nodes=model.NODES
    report={'grid_power':model.GRID_POWER,'grid':[],'time':[]}
    for nodes in [41,81,161,321]:
        model.NODES=nodes
        q3=model.simulate_fixed(environment,model.property_q23,None,10,60,True)
        q4=model.simulate_moving(environment,radius,10,60)
        record={'nodes':nodes,'q3_h':q3['threshold_time_s']/3600,'q4_h':q4['threshold_time_s']/3600}
        report['grid'].append(record);print(record,flush=True)
        (model.RESULTS_DIR/'numerical_verification.json').write_text(json.dumps(report,indent=2))
    model.NODES=saved_nodes
    for dt in [2.,1.]:
        q3=model.simulate_fixed(environment,model.property_q23,None,dt,60,True)
        q4=model.simulate_moving(environment,radius,dt,60)
        record={'dt_s':dt,'nodes':model.NODES,'q3_h':q3['threshold_time_s']/3600,'q4_h':q4['threshold_time_s']/3600}
        report['time'].append(record);print(record,flush=True)
    report['spatial_relative_change_161_to_321']={q:abs(report['grid'][-1][q]-report['grid'][-2][q])/report['grid'][-1][q] for q in ['q3_h','q4_h']}
    report['time_relative_change_2_to_1']={q:abs(report['time'][-1][q]-report['time'][-2][q])/report['time'][-1][q] for q in ['q3_h','q4_h']}
    report['time_tolerance']=1e-4
    report['spatial_tolerance']=1e-3
    report['pass']=all(v<report['spatial_tolerance'] for v in report['spatial_relative_change_161_to_321'].values()) and all(v<report['time_tolerance'] for v in report['time_relative_change_2_to_1'].values())
    (model.RESULTS_DIR/'numerical_verification.json').write_text(json.dumps(report,indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');run()
