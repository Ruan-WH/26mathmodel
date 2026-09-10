"""Check trajectory identity, refinement, closed-system invariance and balances.

Does not write workbooks or regenerate production results.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import solve_drying as m


def run():
    output = {}
    with np.load(m.RESULTS_DIR/'q2/fields.npz') as q2, np.load(m.RESULTS_DIR/'q3/fields.npz') as q3:
        output['q2_q3_exact_shared_trajectory'] = all(
            np.array_equal(q2[key][::60], q3[key])
            for key in ['times_s', 'temperature_c', 'moisture'])
        assert output['q2_q3_exact_shared_trajectory']
        assert np.array_equal(q2['threshold_moisture'],q3['threshold_moisture'])
    env=m.load_environment()
    refinement={}
    original_nodes=m.NODES
    try:
        for q,prop,end in [(1,m.property_q1,1800.),(2,m.property_q23,10800.)]:
            results=[]
            for n in [161,321]:
                m.NODES=n
                results.append(m.simulate_fixed(env,prop,end,1.,60.,False))
            refinement[f'q{q}']={
                'maximum_output_temperature_difference_c':float(np.max(np.abs(results[0]['temperature_c']-results[1]['temperature_c']))),
                'maximum_output_moisture_difference':float(np.max(np.abs(results[0]['moisture']-results[1]['moisture'])))}
            assert refinement[f'q{q}']['maximum_output_temperature_difference_c']<1e-3
            assert refinement[f'q{q}']['maximum_output_moisture_difference']<1e-4
    finally:m.NODES=original_nodes
    output['short_term_refinement_161_to_321_dt1']=refinement
    # Zero exchange and a uniform field must remain unchanged even as R shrinks.
    old_t=np.full(m.NODES,m.INITIAL_T);old_c=np.full(m.NODES,1.2)
    t=old_t.copy();c=old_c.copy();b=m.new_balance()
    for radius in np.linspace(.02,.012,21):
        t,c,_=m.advance_coupled(t,c,10.,radius,0.,m.INITIAL_T,1.2,m.property_q4,True,balance=b)
    output['uniform_material_field_temperature_error']=float(np.max(np.abs(t-old_t)))
    output['uniform_material_field_moisture_error']=float(np.max(np.abs(c-old_c)))
    assert output['uniform_material_field_temperature_error']<1e-8
    assert output['uniform_material_field_moisture_error']<1e-10
    output['production_balances']={}
    for q in range(1,5):
        summary=json.loads((m.RESULTS_DIR/f'q{q}/summary.json').read_text(encoding='utf-8'))
        output['production_balances'][f'q{q}']=summary['balance']
        assert summary['balance']['cumulative_mass_equation_residual']<1e-9
        assert summary['balance']['maximum_step_heat_equation_residual']<1e-10
    output['scope']='Mass balance of implemented dry-reference equation; effective heat equation, not total enthalpy.'
    output['source_sha256']={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['solve_drying.py','validate_long_2d.py','run_sensitivity.py']}
    output['pass']=True
    (m.RESULTS_DIR/'revision_checks.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':run()
