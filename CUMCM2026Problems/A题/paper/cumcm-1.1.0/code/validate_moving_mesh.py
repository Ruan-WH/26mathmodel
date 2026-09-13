# File: code/validate_moving_mesh.py
"""Independent physical-radius moving-control-volume validation of Q4.

No transformed differential operator or R**(-2) enters the physical solver.
The reference path calls the unchanged fixed-domain advance_coupled routine.
Only outputs under results/q4/validation_moving_mesh are written here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
import numpy as np
from scipy.linalg import solve_banded
import solve_drying as main

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/q4/validation_moving_mesh'
TOL_T, TOL_C, MAX_IT = 1e-8, 1e-10, 30


def physical_geometry(nodes: np.ndarray) -> dict:
    """Physical annuli, per unit axial length; centre and surface half-cells."""
    bounds = np.r_[0.0, (nodes[:-1] + nodes[1:]) / 2.0, nodes[-1]]
    # Factored square difference avoids cancellation in the thin surface cell.
    volumes = math.pi * np.diff(bounds) * (bounds[1:] + bounds[:-1])
    assert np.all(np.diff(nodes) > 0) and np.all(volumes > 0)
    return dict(nodes=nodes, bounds=bounds, volumes=volumes,
                areas=2.0 * math.pi * bounds, distances=np.diff(nodes))


def mesh_motion(old: dict, new: dict, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """Swept-volume flux and discrete GCL residual, computed at every face."""
    speed = (new['bounds'] - old['bounds']) / dt
    average_area = math.pi * (new['bounds'] + old['bounds'])
    swept_flux = average_area * speed
    residual = new['volumes'] - old['volumes'] - dt * np.diff(swept_flux)
    return speed, residual


def solve_physical_inventory(old_value, old_capacity, new_capacity,
                             conductivity, geometry, dt, transfer, ambient,
                             inventory_correction=None):
    """Solve extensive inventory balance with physical area / distance fluxes.

    capacity has units inventory per unit scalar (e.g. dry mass per axial m).
    inventory_correction is an extensive change, not an advection coefficient.
    """
    g = geometry
    face_k = 0.5 * (conductivity[:-1] + conductivity[1:])
    conductance = g['areas'][1:-1] * face_k / g['distances']
    surface = g['areas'][-1] * transfer
    diagonal = new_capacity / dt
    diagonal = diagonal.copy()
    diagonal[:-1] += conductance
    diagonal[1:] += conductance
    diagonal[-1] += surface
    rhs = old_capacity * old_value / dt
    if inventory_correction is not None:
        rhs += inventory_correction / dt
    rhs[-1] += surface * ambient
    band = np.zeros((3, len(old_value)))
    band[0, 1:] = -conductance
    band[1] = diagonal
    band[2, :-1] = -conductance
    result = solve_banded((1, 1), band, rhs, check_finite=False)
    return result, conductance, surface


def advance_moving_control_volumes(old_t, old_c, old_g, new_g, dry_mass_total,
                                  dt, ambient_t, ambient_c,
                                  heat_transfer=main.H_T, mass_transfer=main.H_M):
    """Picard iteration for co-moving material cells (v_s=w).

    Water: d(M_d C)/dt + sum(rho_d D A grad C) + boundary loss = 0.
    Heat: preserve the existing effective a D_t T equation. Its extensive
    representation requires T_old * delta(a V), rather than conserving a V T
    without a source. This correction includes geometry AND variable storage.
    """
    rho_d_old = dry_mass_total / old_g['volumes'].sum()
    rho_d_new = dry_mass_total / new_g['volumes'].sum()
    mass_old = rho_d_old * old_g['volumes']
    mass_new = rho_d_new * new_g['volumes']
    old_rho, old_cp, _, _ = main.property_q4(old_t, old_c)
    old_heat_capacity = old_rho * old_cp * old_g['volumes']
    t, c = old_t.copy(), old_c.copy()
    for iteration in range(1, MAX_IT + 1):
        rho, cp, k, _ = main.property_q4(t, c)
        new_heat_capacity = rho * cp * new_g['volumes']
        correction = old_t * (new_heat_capacity - old_heat_capacity)
        t_next, _, heat_surface = solve_physical_inventory(
            old_t, old_heat_capacity, new_heat_capacity, k, new_g, dt,
            heat_transfer, ambient_t, inventory_correction=correction)
        _, _, _, diffusivity = main.property_q4(t_next, c)
        c_next, _, water_surface = solve_physical_inventory(
            old_c, mass_old, mass_new, rho_d_new * diffusivity, new_g, dt,
            rho_d_new * mass_transfer, ambient_c)
        error_t = np.max(np.abs(t_next - t))
        error_c = np.max(np.abs(c_next - c))
        t, c = t_next, c_next
        if error_t < TOL_T and error_c < TOL_C:
            break
    else:
        raise RuntimeError(f'Physical Picard failed: {error_t=}, {error_c=}')
    if not np.isfinite(t).all() or not np.isfinite(c).all():
        raise FloatingPointError('Nonfinite physical solution')
    if c.min() < -1e-10 or c.max() > main.INITIAL_C + 1e-8:
        raise FloatingPointError('Moisture outside physical bounds')
    water_change = np.sum(mass_new * c - mass_old * old_c)
    water_loss = dt * water_surface * (c[-1] - ambient_c)
    # Report BOTH extensive-inventory closure and effective-heat closure.
    heat_inventory_change = np.sum(new_heat_capacity * t - old_heat_capacity * old_t)
    heat_correction = np.sum(correction)
    heat_loss = dt * heat_surface * (t[-1] - ambient_t)
    return t, c, iteration, dict(
        water_change=float(water_change), water_loss=float(water_loss),
        water_residual=float(water_change + water_loss),
        dry_cell_change=float(np.max(np.abs(mass_new - mass_old))),
        heat_residual=float(heat_inventory_change - heat_correction + heat_loss),
        heat_reference=float(main.INITIAL_T * new_heat_capacity.sum()))


def preservation_manifest():
    files = [ROOT/'code/solve_drying.py', ROOT/'code/write_results.py']
    files += list((ROOT/'results').rglob('*.npz')) + list((ROOT/'results').rglob('*.json'))
    files += list(ROOT.rglob('result4.xlsx'))
    for directory in ['figures', 'drawio', 'paper/cumcm-1.1.0/figures']:
        files += list((ROOT/directory).glob('*'))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files if p.is_file() and OUT not in p.parents}


def check_preservation(before):
    changed = [k for k,v in before.items()
               if hashlib.sha256((ROOT/k).read_bytes()).hexdigest() != v]
    if changed:
        raise RuntimeError(f'Protected files changed: {changed}')
    return len(before)


def run_checks():
    """Isolated physics tests: GCL, insulated material, stationary-grid limit."""
    xi=main.radial_grid(main.NODES)
    g0=physical_geometry(.02*xi); g1=physical_geometry(.013*xi)
    _,res=mesh_motion(g0,g1,1.0)
    mass=g0['volumes'].sum()  # rho_d(0)=1; arbitrary normalization cancels.
    tt=np.full(main.NODES,28.0); cc=np.full(main.NODES,2.55)
    t,c,_,diag=advance_moving_control_volumes(tt,cc,g0,g1,mass,1,28,0,
                                           heat_transfer=0,mass_transfer=0)
    assert np.max(np.abs(c-cc)) < 1e-9
    assert np.max(np.abs(t-tt)) < 1e-7
    assert np.max(np.abs(res)) / mass < 1e-12
    # Smooth nonuniform state, zero mesh motion: same physical PDE as baseline.
    tt=28+4*xi**2; cc=2.55-.5*xi**2
    tp,cp,_,_=advance_moving_control_volumes(tt,cc,g0,g0,mass,1,40,.03)
    tr,cr,_=main.advance_coupled(tt,cc,1,.02,0,40,.03,main.property_q4,False)
    assert np.max(np.abs(tp-tr))<1e-7
    assert np.max(np.abs(cp-cr))<1e-9
    return dict(gcl_normalized_max=float(np.max(np.abs(res))/mass),
                insulated_temperature_max_error=float(np.max(np.abs(t-28))),
                insulated_moisture_max_error=float(np.max(np.abs(c-2.55))),
                stationary_temperature_max_error=float(np.max(np.abs(tp-tr))),
                stationary_moisture_max_error=float(np.max(np.abs(cp-cr))))


def simulate_moving_mesh(dt_s=1.0, max_time_s=259200.0):
    """Integrate both implementations independently on the same time levels.

    Save full 161-node fields every minute and centre/surface/errors every step.
    No reference state is injected into the physical iteration.
    """
    env=main.load_environment(); radius=main.load_radius_history()
    xi=main.radial_grid(main.NODES)
    geometry=physical_geometry(radius.values(0)[0]*xi)
    dry_mass_total=geometry['volumes'].sum()
    t_map=np.full(main.NODES,main.INITIAL_T); c_map=np.full(main.NODES,main.INITIAL_C)
    t_mov=t_map.copy(); c_mov=c_map.copy()
    events={}
    times=[0.0]; radii=[.02]
    fields_t_map=[t_map.copy()]; fields_t_mov=[t_mov.copy()]
    fields_c_map=[c_map.copy()]; fields_c_mov=[c_mov.copy()]
    trace=[[0.0,c_map[0],c_mov[0],c_map[-1],c_mov[-1],0.0,0.0,0.0]]
    balances=dict(water_change=0.,water_loss=0.,maximum_step_water_residual=0.,
                  maximum_heat_residual=0.,maximum_dry_cell_relative_drift=0.,
                  maximum_gcl_residual=0.,max_relative_mesh_speed=0.)
    iters=[0,0]; iter_sum=np.zeros(2); monotone=True
    tnow=0.0; next_output=60.0; start=time.perf_counter()
    while tnow < min(max_time_s,float(radius.time_s[-1]))-1e-8:
        step=min(dt_s,next_output-tnow,max_time_s-tnow)
        newtime=tnow+step
        r,r_dot=radius.values(newtime); te,ce=env.values(newtime)
        new_geometry=physical_geometry(r*xi)
        speed,gcl=mesh_motion(geometry,new_geometry,step)
        # Solid faces follow the identical trajectories. The relative flux
        # rho_d C (v_s-w) A is identically zero, not silently omitted.
        solid_face_speed=speed.copy()
        balances['max_relative_mesh_speed']=max(balances['max_relative_mesh_speed'],
                                               float(np.max(abs(solid_face_speed-speed))))
        old_t_map,old_c_map=t_map,c_map
        old_t_mov,old_c_mov=t_mov,c_mov
        t_map,c_map,im=main.advance_coupled(t_map,c_map,step,r,0.0,te,ce,main.property_q4,True)
        t_mov,c_mov,ip,diag=advance_moving_control_volumes(
            t_mov,c_mov,geometry,new_geometry,dry_mass_total,step,te,ce)
        for name,oldt,oldc,tt,cc in [('mapping',old_t_map,old_c_map,t_map,c_map),
                                   ('moving_mesh',old_t_mov,old_c_mov,t_mov,c_mov)]:
            if name not in events and oldc.max()>main.THRESHOLD_C>=cc.max():
                fraction=(oldc.max()-main.THRESHOLD_C)/(oldc.max()-cc.max())
                et=tnow+fraction*step
                events[name]=dict(time_s=et,time_h=et/3600,
                                  temperature=oldt+fraction*(tt-oldt),
                                  moisture=oldc+fraction*(cc-oldc),
                                  radius_m=radius.values(et)[0])
        reference=dry_mass_total*main.INITIAL_C
        balances['water_change']+=diag['water_change']/reference
        balances['water_loss']+=diag['water_loss']/reference
        balances['maximum_step_water_residual']=max(balances['maximum_step_water_residual'],abs(diag['water_residual'])/reference)
        balances['maximum_heat_residual']=max(balances['maximum_heat_residual'],abs(diag['heat_residual'])/diag['heat_reference'])
        balances['maximum_dry_cell_relative_drift']=max(balances['maximum_dry_cell_relative_drift'],float(np.max(abs((dry_mass_total/new_geometry['volumes'].sum())*new_geometry['volumes']/(geometry['volumes']*(dry_mass_total/geometry['volumes'].sum()))-1))))
        balances['maximum_gcl_residual']=max(balances['maximum_gcl_residual'],float(np.max(abs(gcl)))/geometry['volumes'].sum())
        monotone=monotone and bool(np.max(np.diff(c_mov))<=2e-9)
        iters=[max(iters[0],im),max(iters[1],ip)]; iter_sum += [im,ip]
        dc=float(np.max(abs(c_map-c_mov))); dtemp=float(np.max(abs(t_map-t_mov)))
        trace.append([newtime,c_map[0],c_mov[0],c_map[-1],c_mov[-1],dc,dtemp,abs(c_map[0]-c_mov[0])])
        tnow=newtime;geometry=new_geometry
        if tnow>=next_output-1e-8:
            times.append(tnow);radii.append(r)
            fields_t_map.append(t_map.copy());fields_t_mov.append(t_mov.copy())
            fields_c_map.append(c_map.copy());fields_c_mov.append(c_mov.copy())
            next_output += 60.0
            if int(round(tnow))%21600==0:
                print(f'{tnow/3600:.0f} h: centre C={c_mov[0]:.9f}, max |dC|={dc:.3e}, elapsed={time.perf_counter()-start:.1f}s',flush=True)
            if len(events)==2:
                break
    arrays=dict(times_s=np.array(times),radii_m=np.array(radii),xi=xi,
                mapping_temperature=np.array(fields_t_map),moving_temperature=np.array(fields_t_mov),
                mapping_moisture=np.array(fields_c_map),moving_moisture=np.array(fields_c_mov),
                step_trace=np.array(trace))
    for name,e in events.items():
        for key in ['temperature','moisture']:
            arrays[f'{name}_event_{key}']=e[key]
    np.savez_compressed(OUT/'fields.npz',**arrays)
    balances['cumulative_water_residual']=abs(balances['water_change']+balances['water_loss'])
    report=dict(dt_s=dt_s,nodes=main.NODES,tolerances=dict(temperature=TOL_T,moisture=TOL_C,max_iterations=MAX_IT),
                elapsed_seconds=time.perf_counter()-start,time_steps=len(trace)-1,
                picard_max=dict(mapping=iters[0],moving_mesh=iters[1]),
                picard_mean=dict(mapping=float(iter_sum[0]/(len(trace)-1)),moving_mesh=float(iter_sum[1]/(len(trace)-1))),
                monotone_profiles=monotone,balances=balances,
                events={name:{k:float(v) for k,v in e.items() if k not in ['temperature','moisture']} for name,e in events.items()},
                max_abs_moisture_field_difference=float(arrays['step_trace'][:,5].max()),
                max_abs_temperature_field_difference=float(arrays['step_trace'][:,6].max()),
                max_abs_center_moisture_difference=float(arrays['step_trace'][:,7].max()))
    if len(events)==2:
        delta=abs(events['mapping']['time_s']-events['moving_mesh']['time_s'])
        report['drying_time_abs_difference_s']=delta
        report['drying_time_relative_difference']=delta/events['mapping']['time_s']
        report['event_comparison_note']='Own-event profiles and common mapping-event centre/surface values are distinguished; trajectories compare identical time levels.'
    (OUT/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return arrays,report


def write_comparisons(arrays,report):
    rows=[]
    def add(metric,a,b,unit):
        rows.append(dict(metric=metric,unit=unit,mapping=float(a),moving_mesh=float(b),
                         absolute_difference=abs(float(a)-float(b)),
                         relative_difference=abs(float(a)-float(b))/abs(float(a)) if a else None))
    if len(report['events'])!=2:
        return
    add('drying_time',report['events']['mapping']['time_h'],report['events']['moving_mesh']['time_h'],'h')
    profiles=[]
    for label,seconds in [('6h',21600),('24h',86400),('48h',172800),('own_event',None)]:
        if seconds is None:
            ca=arrays['mapping_event_moisture'];cb=arrays['moving_mesh_event_moisture']
            ta=arrays['mapping_event_temperature'];tb=arrays['moving_mesh_event_temperature']
            ra=report['events']['mapping']['radius_m']; rb=report['events']['moving_mesh']['radius_m']
        else:
            i=int(np.flatnonzero(arrays['times_s']==seconds)[0])
            ca=arrays['mapping_moisture'][i];cb=arrays['moving_moisture'][i]
            ta=arrays['mapping_temperature'][i];tb=arrays['moving_temperature'][i]
            ra=rb=arrays['radii_m'][i]
        for point,k in [('center',0),('surface',-1)]:
            add(f'{label}_{point}_moisture',ca[k],cb[k],'kg/kg')
        for j,xi in enumerate(arrays['xi']):
            profiles.append(dict(time_label=label,node=j,r_mapping_cm=100*ra*xi,r_moving_cm=100*rb*xi,
                                 C_mapping=ca[j],C_moving=cb[j],T_mapping=ta[j],T_moving=tb[j]))
    shared_time=report['events']['mapping']['time_s']
    trace=arrays['step_trace']
    for point,ia,ib in [('center',1,2),('surface',3,4)]:
        add(f'common_event_{point}_moisture',np.interp(shared_time,trace[:,0],trace[:,ia]),
            np.interp(shared_time,trace[:,0],trace[:,ib]),'kg/kg')
    # Compute the time relative difference in seconds consistently with summary.
    rows[0]['relative_difference']=report['drying_time_relative_difference']
    for name,data in [('comparison.csv',rows),('profiles.csv',profiles)]:
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as stream:
            writer=csv.DictWriter(stream,fieldnames=data[0].keys());writer.writeheader();writer.writerows(data)
    text='| Metric | Unit | Fixed mapping | Physical moving mesh | Relative difference |\n|---|---|---:|---:|---:|\n'
    for row in rows:
        text+=f"| {row['metric']} | {row['unit']} | {row['mapping']:.12g} | {row['moving_mesh']:.12g} | {row['relative_difference']:.4e} |\n"
    (OUT/'comparison.md').write_text(text,encoding='utf8')
    # Match regenerated reference fields to the pre-existing output, without
    # changing original files or using them as integration states.
    old=np.load(ROOT/'results/q4/fields.npz')
    source=json.loads((ROOT/'results/q4/summary.json').read_text(encoding='utf8'))
    assert np.array_equal(old['times_s'],arrays['times_s'])
    mapped_c=np.array([np.interp(old['xi'],arrays['xi'],row) for row in arrays['mapping_moisture']])
    mapped_t=np.array([np.interp(old['xi'],arrays['xi'],row) for row in arrays['mapping_temperature']])
    reproduction=dict(max_C_difference=float(np.max(abs(mapped_c-old['moisture']))),
                      max_T_difference=float(np.max(abs(mapped_t-old['temperature_c']))),
                      drying_time_difference_s=abs(report['events']['mapping']['time_s']-source['drying_time_s']))
    (OUT/'reference_reproduction.json').write_text(json.dumps(reproduction,indent=2),encoding='utf8')
    assert reproduction['max_C_difference']<1e-12 and reproduction['max_T_difference']<1e-10
    assert reproduction['drying_time_difference_s']<1e-6


def run():
    sys.stdout.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    before=preservation_manifest()
    (OUT/'protected_files_sha256.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf8')
    checks=run_checks();(OUT/'unit_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    print('Physics checks:',checks,flush=True)
    if not args.check_only:
        arrays,report=simulate_moving_mesh()
        write_comparisons(arrays,report)
        assert len(report['events'])==2 and report['monotone_profiles']
        print(json.dumps(report,indent=2),flush=True)
    print('Protected files verified:',check_preservation(before),flush=True)


if __name__=='__main__':
    run()
