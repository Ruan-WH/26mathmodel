"""Field-grid comparison, early-time step comparison and Q2/Q3 prefix agreement."""
import json
import numpy as np
import solve_drying as s


def run():
    env=s.load_environment();rad=s.load_radius_history();report={}
    for q in [1,2]:
        baseline=np.load(s.RESULTS_DIR/f'q{q}'/'fields.npz')
        fine=s.simulate_fixed(env,s.property_q1 if q==1 else s.property_q23,
                              1800 if q==1 else 10800,1,1,False,nodes=641)
        # Graded 641 -> 321 grids have coinciding every-second nodes.
        sampled=fine['moisture'][:,::2];sampled_t=fine['temperature_c'][:,::2]
        report[f'q{q}_321_vs_641']={
            'max_abs_T':float(np.max(abs(sampled_t-baseline['temperature_c']))),
            'max_abs_C':float(np.max(abs(sampled-baseline['moisture']))),
            'grid_power':s.GRID_POWER}
        print(q,report[f'q{q}_321_vs_641'],flush=True)
        s.write_summary(s.RESULTS_DIR/'field_verification.json',report)
    q2=np.load(s.RESULTS_DIR/'q2/fields.npz');q3=np.load(s.RESULTS_DIR/'q3/fields.npz')
    mask=q3['times_s']<=10800;index=q3['times_s'][mask].astype(int)
    report['q2_q3_shared_prefix']={
        'max_abs_T':float(np.max(abs(q2['temperature_c'][index]-q3['temperature_c'][mask]))),
        'max_abs_C':float(np.max(abs(q2['moisture'][index]-q3['moisture'][mask])))}
    for q in [3,4]:
        fine=s.simulate_fixed(env,s.property_q23,None,10,3600,True,early_dt_s=.5) if q==3 else s.simulate_moving(env,rad,10,3600,early_dt_s=.5)
        baseline=json.loads((s.RESULTS_DIR/f'q{q}/summary.json').read_text(encoding='utf-8'))
        report[f'q{q}_early_dt_half']={'time_h':fine['threshold_time_s']/3600,
            'difference_s':fine['threshold_time_s']-baseline['drying_time_s']}
        print(q,report[f'q{q}_early_dt_half'],flush=True)
        s.write_summary(s.RESULTS_DIR/'field_verification.json',report)

if __name__=='__main__':
    run()
