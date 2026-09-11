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
    # COMSOL rounds long CSV time labels; recover exact values from the study schedule.
    # Recover the requested output times from the model's study definition.
    study = (path.parent / "Q4Automation.java").read_text(encoding="utf-8")
    schedule = re.search(r'\.set\("tlist", "range\(([^)]+)\) ([^"]+)"\)', study)
    if schedule is None:
        raise ValueError("Cannot identify the COMSOL study output times")
    start, step, end = map(float, schedule.group(1).split(","))
    requested = np.r_[np.arange(start, end + step / 2, step),
                      [float(value) for value in schedule.group(2).split()]]
    if len(requested) != len(times) or not np.allclose(requested, times, rtol=0, atol=5):
        raise ValueError("COMSOL CSV columns do not match the study output schedule")
    return names, data, requested


def comparison_times(event_time_s):
    return np.array([21600., 43200., 86400., 129600., 172800., event_time_s])


def baseline_profile(base, key, time_s, event_time_s):
    """Use the native-grid event profile or interpolate at the requested time."""
    if abs(time_s - event_time_s) < 1e-6:
        return base["threshold_" + key]
    times = base["times_s"]
    index = int(np.searchsorted(times, time_s))
    if index < len(times) and abs(times[index] - time_s) < 1e-8:
        return base[key][index]
    if index == 0 or index == len(times):
        raise ValueError("Requested comparison time is outside the baseline trajectory")
    fraction = (time_s - times[index - 1]) / (times[index] - times[index - 1])
    return (1 - fraction) * base[key][index - 1] + fraction * base[key][index]


def main():
    names, data, times = read_comsol_wide(HERE / "q4_comsol_profiles.csv")
    x = data[:, 0]
    temp = data[:, 2::4].T
    moist = data[:, 3::4].T
    rphys = data[:, 4::4].T
    radius = data[0, 5::4]

    with np.load(BASELINE) as archive:
        base = {key: archive[key] for key in archive.files}
    base_xi = base["xi"]
    reference_summary = json.loads(BASELINE.with_name("summary.json").read_text(encoding="utf-8"))
    event_time = reference_summary["drying_time_s"]
    compare_times = comparison_times(event_time)
    records = []
    all_dt, all_dc = [], []
    for target in compare_times:
        ic = int(np.argmin(np.abs(times - target)))
        if abs(times[ic] - target) > 1e-6:
            raise ValueError("COMSOL output is missing a requested comparison time")
        bt = np.interp(x / 0.02, base_xi, baseline_profile(base, "temperature_c", target, event_time))
        bc = np.interp(x / 0.02, base_xi, baseline_profile(base, "moisture", target, event_time))
        dt = np.abs(temp[ic] - bt)
        dc = np.abs(moist[ic] - bc)
        all_dt.extend(dt)
        all_dc.extend(dc)
        records.append({
            "time_h": float(target / 3600),
            "comparison_time_s": float(target),
            "comsol_output_time_s": float(times[ic]),
            "radius_cm": float(radius[ic] * 100),
            "comsol_center_moisture": float(moist[ic, 0]),
            "baseline_center_moisture": float(bc[0]),
            "comsol_surface_moisture": float(moist[ic, -1]),
            "baseline_surface_moisture": float(bc[-1]),
            "max_abs_temperature_difference_C": float(dt.max()),
            "max_abs_moisture_difference": float(dc.max()),
            "maximum_difference_xi": float(x[int(np.argmax(dc))] / 0.02),
        })

    summary = {
        "comsol_version": "6.3.0.290",
        "formulation": "uniform material shrinkage in a fixed radial reference coordinate",
        "output_times": int(len(times)),
        "radial_sample_points": int(len(x)),
        "baseline_saved_nodes": int(len(base_xi)),
        "time_source": "Q4Automation.java study output schedule; CSV header times are rounded",
        "event_comparison_scope": "Concentrations at the FVM event time; not an independent COMSOL event search",
        "comparison": records,
        "overall_max_abs_temperature_difference_C": float(max(all_dt)),
        "overall_max_abs_moisture_difference": float(max(all_dc)),
        "event_time_h": event_time / 3600,
        "event_comsol_center_moisture": float(moist[np.argmin(abs(times-event_time)), 0]),
        "event_comsol_surface_moisture": float(moist[np.argmin(abs(times-event_time)), -1]),
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
