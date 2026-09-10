"""Two-dimensional axisymmetric check for the one-dimensional Q1 model."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from solve_drying import (
    H_M,
    H_T,
    INITIAL_C,
    INITIAL_T,
    NODES,
    RESULTS_DIR,
    R_FIXED,
    load_environment,
    property_q1,
    simulate_fixed,
)


LENGTH = 0.25


def geometry(nr: int = NODES, nz: int = 26):
    r = np.linspace(0.0, R_FIXED, nr)
    z = np.linspace(0.0, LENGTH / 2.0, nz)
    r_faces = 0.5 * (r[:-1] + r[1:])
    r_lo = np.concatenate(([0.0], r_faces))
    r_hi = np.concatenate((r_faces, [R_FIXED]))
    annular_area = math.pi * (r_hi**2 - r_lo**2)
    z_faces = 0.5 * (z[:-1] + z[1:])
    z_lo = np.concatenate(([0.0], z_faces))
    z_hi = np.concatenate((z_faces, [LENGTH / 2.0]))
    z_width = z_hi - z_lo
    volume = annular_area[:, None] * z_width[None, :]
    return r, z, annular_area, z_width, volume


def implicit_2d(
    old: np.ndarray,
    storage: np.ndarray,
    conductivity: np.ndarray,
    dt: float,
    boundary_coefficient: float,
    boundary_value: float,
    r: np.ndarray,
    z: np.ndarray,
    annular_area: np.ndarray,
    z_width: np.ndarray,
    volume: np.ndarray,
) -> np.ndarray:
    nr, nz = old.shape
    dr = r[1] - r[0]
    dz = z[1] - z[0]
    count = nr * nz
    diagonal = (storage * volume / dt).ravel().copy()
    rhs = (storage * volume / dt * old).ravel()
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []

    def add_edge(first: int, second: int, conductance: float) -> None:
        diagonal[first] += conductance
        diagonal[second] += conductance
        rows.extend((first, second))
        cols.extend((second, first))
        data.extend((-conductance, -conductance))

    radial_faces = 0.5 * (r[:-1] + r[1:])
    for i in range(nr - 1):
        for j in range(nz):
            first = i * nz + j
            second = (i + 1) * nz + j
            k_face = 0.5 * (conductivity[i, j] + conductivity[i + 1, j])
            area = 2.0 * math.pi * radial_faces[i] * z_width[j]
            add_edge(first, second, area * k_face / dr)

    for i in range(nr):
        for j in range(nz - 1):
            first = i * nz + j
            second = i * nz + j + 1
            k_face = 0.5 * (conductivity[i, j] + conductivity[i, j + 1])
            add_edge(first, second, annular_area[i] * k_face / dz)

    # Cylindrical side wall.
    for j in range(nz):
        index = (nr - 1) * nz + j
        boundary = boundary_coefficient * 2.0 * math.pi * R_FIXED * z_width[j]
        diagonal[index] += boundary
        rhs[index] += boundary * boundary_value

    # One physical end face; z=0 is the cylinder mid-plane symmetry boundary.
    for i in range(nr):
        index = i * nz + (nz - 1)
        boundary = boundary_coefficient * annular_area[i]
        diagonal[index] += boundary
        rhs[index] += boundary * boundary_value

    rows.extend(range(count))
    cols.extend(range(count))
    data.extend(diagonal.tolist())
    matrix = coo_matrix((data, (rows, cols)), shape=(count, count)).tocsr()
    return np.asarray(spsolve(matrix, rhs)).reshape(nr, nz)


def run() -> None:
    environment = load_environment()
    r, z, annular_area, z_width, volume = geometry()
    temperature = np.full((len(r), len(z)), INITIAL_T)
    moisture = np.full_like(temperature, INITIAL_C)
    dt = 10.0
    picard_max = 0
    for time_s in np.arange(dt, 1800.0 + dt, dt):
        ambient_t, ambient_c = environment.values(float(time_s))
        guess_t = temperature.copy()
        guess_c = moisture.copy()
        for iteration in range(1, 31):
            rho, cp, k, _ = property_q1(guess_t, guess_c)
            next_t = implicit_2d(
                temperature,
                rho * cp,
                k,
                dt,
                H_T,
                ambient_t,
                r,
                z,
                annular_area,
                z_width,
                volume,
            )
            _, _, _, diffusivity = property_q1(next_t, guess_c)
            next_c = implicit_2d(
                moisture,
                np.ones_like(moisture),
                diffusivity,
                dt,
                H_M,
                ambient_c,
                r,
                z,
                annular_area,
                z_width,
                volume,
            )
            error_t = float(np.max(np.abs(next_t - guess_t)))
            error_c = float(np.max(np.abs(next_c - guess_c)))
            guess_t, guess_c = next_t, next_c
            if error_t < 1e-8 and error_c < 1e-10:
                break
        else:
            raise RuntimeError("2D Picard iteration failed.")
        picard_max = max(picard_max, iteration)
        temperature, moisture = guess_t, guess_c

    one_dimensional = simulate_fixed(
        environment,
        property_q1,
        end_time_s=1800.0,
        dt_s=10.0,
        output_interval_s=1800.0,
        stop_at_threshold=False,
    )
    one_t = np.asarray(one_dimensional["temperature_c"])[-1]
    one_c = np.asarray(one_dimensional["moisture"])[-1]
    mid_t = temperature[:, 0]
    mid_c = moisture[:, 0]
    end_t = temperature[:, -1]
    end_c = moisture[:, -1]
    report = {
        "grid": {"radial_nodes": len(r), "half_axial_nodes": len(z), "dt_s": dt},
        "midplane_max_abs_temperature_difference_c": float(np.max(np.abs(mid_t - one_t))),
        "midplane_max_abs_moisture_difference": float(np.max(np.abs(mid_c - one_c))),
        "end_to_midplane_max_temperature_difference_c": float(np.max(np.abs(end_t - mid_t))),
        "end_to_midplane_max_moisture_difference": float(np.max(np.abs(end_c - mid_c))),
        "one_dimensional_midplane_pass": bool(
            np.max(np.abs(mid_t - one_t)) < 0.1
            and np.max(np.abs(mid_c - one_c)) < 1e-3
        ),
        "picard_max": picard_max,
    }
    output = RESULTS_DIR / "q1" / "validation_2d.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
