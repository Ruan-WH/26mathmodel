from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "results" / "q4" / "fields.npz"


def read_comsol_wide(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        lines = [line for line in f if not line.startswith("%") or line.startswith("% X,")]
    header = next(line[2:].strip() for line in lines if line.startswith("% X,"))
    rows = [line for line in lines if not line.startswith("%")]
    names = next(csv.reader([header]))
    data = np.asarray([[float(x) for x in row] for row in csv.reader(rows)], dtype=float)
    times = []
    for j in range(2, len(names), 4):
        m = re.search(r"@ t=([0-9.Ee+-]+)", names[j])
        if not m:
            raise ValueError(names[j])
        times.append(float(m.group(1)))
    return names, data, np.asarray(times)


def main():
    names, data, times = read_comsol_wide(HERE / "q4_comsol_profiles.csv")
    x = data[:, 0]
    temp = data[:, 2::4].T
    moist = data[:, 3::4].T
    rphys = data[:, 4::4].T
    radius = data[0, 5::4]

    base = np.load(BASELINE)
    base_times = base["times_s"]
    base_xi = base["xi"]
    compare_times = np.array([21600., 43200., 86400., 129600., 172800., 182956.80447014328])
    records = []
    all_dt, all_dc = [], []
    for target in compare_times:
        ic = int(np.argmin(np.abs(times - target)))
        ib = int(np.argmin(np.abs(base_times - target)))
        bt = np.interp(x / 0.02, base_xi, base["temperature_c"][ib])
        bc = np.interp(x / 0.02, base_xi, base["moisture"][ib])
        dt = np.abs(temp[ic] - bt)
        dc = np.abs(moist[ic] - bc)
        all_dt.extend(dt)
        all_dc.extend(dc)
        records.append({
            "time_h": float(target / 3600),
            "radius_cm": float(radius[ic] * 100),
            "comsol_center_moisture": float(moist[ic, 0]),
            "baseline_center_moisture": float(bc[0]),
            "comsol_surface_moisture": float(moist[ic, -1]),
            "baseline_surface_moisture": float(bc[-1]),
            "max_abs_temperature_difference_C": float(dt.max()),
            "max_abs_moisture_difference": float(dc.max()),
        })

    summary = {
        "comsol_version": "6.3.0.290",
        "formulation": "uniform material shrinkage in a fixed radial reference coordinate",
        "output_times": int(len(times)),
        "radial_sample_points": int(len(x)),
        "comparison": records,
        "overall_max_abs_temperature_difference_C": float(max(all_dt)),
        "overall_max_abs_moisture_difference": float(max(all_dc)),
        "event_time_h": 182956.80447014328 / 3600,
        "event_comsol_center_moisture": float(moist[np.argmin(abs(times-182956.80447014328)), 0]),
        "event_comsol_surface_moisture": float(moist[np.argmin(abs(times-182956.80447014328)), -1]),
    }
    (HERE / "q4_comsol_validation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (HERE / "q4_comsol_comparison.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    np.savez_compressed(HERE / "q4_comsol_fields.npz", times_s=times, x_ref_m=x,
                        radii_m=radius, rphys_m=rphys, temperature_c=temp, moisture=moist)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
