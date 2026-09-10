"""Reproduce the graded spatial convergence study after solve_drying.py."""
import json
import solve_drying as s


def run():
    env=s.load_environment(); radius=s.load_radius_history(); rows=[]
    for n in [81,161,321,641]:
        for q in [3,4]:
            if n==s.NODES:
                base=s.RESULTS_DIR/f'q{q}'
                diag=json.loads((base/'diagnostics.json').read_text(encoding='utf-8'))
                assert diag['nodes']==n and diag['grid_power']==s.GRID_POWER
                summary=json.loads((base/'summary.json').read_text(encoding='utf-8'))
                time_h=summary['drying_time_h']
                residual=diag['relative_cumulative_mass_residual']
            else:
                result=(s.simulate_fixed(env,s.property_q23,None,10,3600,True,nodes=n)
                        if q==3 else s.simulate_moving(env,radius,10,3600,nodes=n))
                time_h=result['threshold_time_s']/3600
                residual=result['relative_cumulative_mass_residual']
            row=dict(q=q,nodes=n,grid_power=s.GRID_POWER,time_h=time_h,mass_residual=residual)
            rows.append(row)
            s.write_summary(s.RESULTS_DIR/'graded_grid_study.json',rows)
            print(json.dumps(row),flush=True)


if __name__=='__main__':
    run()
