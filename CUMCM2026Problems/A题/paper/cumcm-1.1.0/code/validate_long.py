"""Full implicit axisymmetric verification through the drying threshold.

z=0 is the midplane; z=L/2 is the exposed end. Radius may shrink materially.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import solve_drying as model


def run_case(question=3, nr=41, nz=31, dt=60.0, early_dt=10.0):
    env = model.load_environment()
    history = model.load_radius_history() if question == 4 else None
    prop = {1: model.property_q1, 3: model.property_q23, 4: model.property_q4}[question]
    xi = model.radial_grid(nr)
    z = np.linspace(0, 0.125, nz)
    annulus, faces = model.node_control_volumes(xi)
    zfaces = (z[:-1] + z[1:]) / 2
    dzwidth = np.diff(np.r_[0, zfaces, z[-1]])
    volume = annulus[:, None] * dzwidth[None, :]
    idx = np.arange(nr * nz).reshape(nr, nz)
    first = np.r_[idx[:-1, :].ravel(), idx[:, :-1].ravel()]
    second = np.r_[idx[1:, :].ravel(), idx[:, 1:].ravel()]
    rows = np.r_[first, second, idx.ravel()]
    cols = np.r_[second, first, idx.ravel()]
    radial_geometry = 2 * math.pi * faces[:, None] * dzwidth / np.diff(xi)[:, None]
    axial_geometry = annulus[:, None] / (z[1] - z[0])
    temp = np.full((nr, nz), model.INITIAL_T)
    moist = np.full_like(temp, model.INITIAL_C)
    t, threshold = 0.0, math.nan
    max_iter = 0
    terminal = 1800 if question == 1 else 72 * 3600
    start = time.perf_counter()

    def advance(old, storage, kr, kz, h, ambient, radius, step):
        edge = np.r_[(radial_geometry * kr / radius**2).ravel(),
                     (axial_geometry * kz).ravel()]
        capacity = (storage * volume / step).ravel()
        diag = capacity + np.bincount(first, edge, minlength=nr*nz) + np.bincount(second, edge, minlength=nr*nz)
        boundary = np.zeros((nr, nz))
        boundary[-1, :] += 2 * math.pi * dzwidth * h / radius
        boundary[:, -1] += annulus * h
        diag += boundary.ravel()
        rhs = capacity * old.ravel() + boundary.ravel() * ambient
        matrix = coo_matrix((np.r_[-edge, -edge, diag], (rows, cols)), shape=(nr*nz, nr*nz)).tocsc()
        return spsolve(matrix, rhs).reshape(nr, nz)

    while t < terminal - 1e-8:
        step = min(early_dt if t < 10800 else dt, terminal - t)
        for knot in (10800, 14400):
            if t < knot:
                step = min(step, knot-t)
        radius = history.values(t+step)[0] if history else model.R_FIXED
        te, ce = env.values(t+step)
        gt, gc = temp.copy(), moist.copy()
        for iteration in range(1, 31):
            rho, cp, k, _ = prop(gt, gc)
            nt = advance(temp, rho*cp, (k[:-1]+k[1:])/2,
                         (k[:, :-1]+k[:, 1:])/2, model.H_T, te, radius, step)
            nc = advance(moist, np.ones_like(gc), model.moisture_faces(nt, gc, prop, 0),
                         model.moisture_faces(nt, gc, prop, 1), model.H_M, ce, radius, step)
            errt, errc = np.max(abs(nt-gt)), np.max(abs(nc-gc))
            gt, gc = nt, nc
            if errt < 1e-7 and errc < 1e-9:
                break
        else:
            raise RuntimeError('2D nonlinear convergence failure')
        max_iter = max(iteration, max_iter)
        before, after = float(np.max(moist)), float(np.max(gc))
        temp, moist = gt, gc
        t += step
        if before > model.THRESHOLD_C >= after:
            threshold = t-step + step * (before-model.THRESHOLD_C)/(before-after)
            break
    if question != 1 and not math.isfinite(threshold):
        raise RuntimeError('2D threshold not reached')
    if question == 4:
        one = model.simulate_moving(env, history, dt, 3600, nodes=nr, early_dt_s=early_dt)
    else:
        one = model.simulate_fixed(env, prop, 1800 if question == 1 else None,
                                  dt, 1800 if question == 1 else 3600,
                                  question != 1, nodes=nr, early_dt_s=early_dt)
    result = dict(question=question, radial_nodes=nr, half_axial_nodes=nz, grid_power=model.GRID_POWER,
                  dt_s=dt, early_dt_s=early_dt, drying_time_2d_h=threshold/3600,
                  drying_time_1d_h=one['threshold_time_s']/3600,
                  difference_s=threshold-one['threshold_time_s'],
                  maximum_location_index=list(map(int, np.unravel_index(np.argmax(moist), moist.shape))),
                  maximum_at_radial_axial_center=bool(np.argmax(moist)==0),
                  picard_max=max_iter, runtime_s=time.perf_counter()-start)
    if question == 1:
        result.update(midplane_max_abs_temperature_difference_c=float(np.max(abs(temp[:,0]-one['temperature_c'][-1]))),
                      midplane_max_abs_moisture_difference=float(np.max(abs(moist[:,0]-one['moisture'][-1]))),
                      end_to_midplane_max_temperature_difference_c=float(np.max(abs(temp[:,-1]-temp[:,0]))),
                      end_to_midplane_max_moisture_difference=float(np.max(abs(moist[:,-1]-moist[:,0]))))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--extended', action='store_true', help='Also refine radial mesh and 2D time step')
    args = parser.parse_args()
    rows=[]
    cases=[(1,41,31,10), (3,41,31,60), (4,41,31,60)]
    if not args.quick:
        cases += [(3,41,61,60), (4,41,61,60)]
    if args.extended:
        cases += [(3,81,61,60), (4,81,61,60), (3,41,31,30), (4,41,31,30)]
    for q,nr,nz,dt in cases:
        row=run_case(q,nr,nz,dt)
        rows.append(row)
        model.write_summary(model.RESULTS_DIR/'validation_2d_long.json',rows)
        print(json.dumps(model.json_ready(row), ensure_ascii=False),flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
