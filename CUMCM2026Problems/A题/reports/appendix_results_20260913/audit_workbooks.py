"""Read-only, cell-by-cell audit. Writes reports here; never saves any workbook."""
from pathlib import Path
import hashlib
import json
import math
import sys
from datetime import datetime

import numpy as np
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def py_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


archives = {}
summaries = {}
for q in range(1, 5):
    with np.load(ROOT / "results" / f"q{q}" / "fields.npz") as z:
        archives[q] = {k: z[k] for k in z.files}
    summaries[q] = json.loads((ROOT / "results" / f"q{q}" / "summary.json").read_text(encoding="utf-8"))

audit = {
    "audit_time_local": datetime.now().isoformat(timespec="seconds"),
    "method": "Fresh openpyxl read-only iteration of every used cell; independent field mapping; no calls to exporter; no workbook writes.",
    "scope": "Q2 user-confirmed 3 h: 1--10800 s. Q1 1--1800 s. Q3/Q4 every 60 s through the first whole minute after the interpolated threshold event.",
    "problem_source": "A题.pdf, all 4 pages read in this audit",
    "exporter_sha256": sha(ROOT / "code" / "write_results.py"),
    "workbooks": [],
}

for q in range(1, 5):
    path = ROOT / "results" / f"result{q}.xlsx"
    template_path = ROOT / "附件" / "附件3" / path.name
    fields_path = ROOT / "results" / f"q{q}" / "fields.npz"
    hashes_before = {"workbook": sha(path), "fields": sha(fields_path), "template": sha(template_path)}
    a = archives[q]
    dt = 1 if q <= 2 else 60
    end = {1: 1800, 2: 10800}.get(q, int(a["times_s"][-1]))
    expected_times = np.arange(dt, end + 1, dt)
    indexes = np.searchsorted(a["times_s"], expected_times)
    source_schedule_ok = np.array_equal(a["times_s"][indexes], expected_times)
    template = load_workbook(template_path, read_only=True, data_only=False)
    book = load_workbook(path, read_only=True, data_only=False)
    expected_sheet_names = ["温度", "水分浓度"] if q <= 2 else ["Sheet1"]
    headers = ["时间/s"] + [round(i / 10, 1) for i in range(21 if q < 4 else 20)]
    if q == 4:
        headers.append("药材表面")
    item = {
        "question": q,
        "path": str(path.relative_to(ROOT)),
        "sha256_before": hashes_before,
        "template_sheets": template.sheetnames,
        "template_first_rows": {s.title: list(next(s.iter_rows(min_row=1, max_row=1, values_only=True))) for s in template},
        "sheet_names_match_template": book.sheetnames == template.sheetnames == expected_sheet_names,
        "header_note": "A1 changed from template's distance/time descriptor to 时间/s; first-row numeric positions retain cm as defined by the problem.",
        "time_start_s": dt,
        "time_end_s": end,
        "interval_s": dt,
        "expected_data_rows_per_sheet": len(expected_times),
        "source_schedule_ok": bool(source_schedule_ok),
        "sheets": {},
    }
    if q < 4:
        grid_ok = np.allclose(a["radius_m"], np.arange(21) * .001, rtol=0, atol=1e-14)
    else:
        n = summaries[q]["numerics"]["nodes"]
        power = summaries[q]["numerics"]["grid_power"]
        grid_ok = np.allclose(a["xi"], 1 - (1 - np.linspace(0, 1, n)) ** power, rtol=0, atol=1e-14)
    item["field_grid_matches_export_rule"] = bool(grid_ok)
    for sheet in book:
        key = "temperature_c" if sheet.title == "温度" else "moisture"
        stats = {
            "rows_including_header": sheet.max_row,
            "columns": sheet.max_column,
            "header_matches_expanded_template": list(next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))) == headers,
            "shape_matches": sheet.max_row == len(expected_times) + 1 and sheet.max_column == 22,
            "data_cells_compared": 0,
            "numeric_value_cells": 0,
            "expected_outside_blank_cells": 0,
            "value_mismatches": 0,
            "time_mismatches": 0,
            "number_format_mismatches": 0,
            "non_numeric_data_cells": 0,
            "formula_or_error_cells": 0,
            "rounding_mismatches": 0,
            "examples": [],
        }
        first_row = None
        last_row = None
        for ri, row in enumerate(sheet.iter_rows(min_row=2), 0):
            values = [c.value for c in row]
            first_row = first_row or values
            last_row = values
            if ri >= len(indexes):
                stats["value_mismatches"] += len(row)
                continue
            ix = indexes[ri]
            if values[0] != int(expected_times[ri]) or not py_number(values[0]):
                stats["time_mismatches"] += 1
            if row[0].number_format != "0":
                stats["number_format_mismatches"] += 1
            if q < 4:
                expected = [round(float(v), 4) for v in a[key][ix]]
            else:
                radius = float(a["radii_m"][ix])
                profile = a["moisture"][ix]
                expected = []
                for j in range(20):
                    position = j * .001
                    if position > radius + 1e-12:
                        expected.append(None)
                    else:
                        # Explicit linear interpolation, independent of exporter np.interp.
                        x = position / radius
                        right = min(max(int(np.searchsorted(a["xi"], x, side="right")), 1), len(a["xi"]) - 1)
                        left = right - 1
                        w = (x - a["xi"][left]) / (a["xi"][right] - a["xi"][left])
                        value = (1 - w) * profile[left] + w * profile[right]
                        expected.append(round(float(value), 4))
                expected.append(round(float(profile[-1]), 4))
            for cell, target in zip(row[1:], expected):
                actual = cell.value
                stats["data_cells_compared"] += 1
                if target is None:
                    stats["expected_outside_blank_cells"] += 1
                else:
                    stats["numeric_value_cells"] += 1
                    if not py_number(actual):
                        stats["non_numeric_data_cells"] += 1
                    elif abs(actual - round(actual, 4)) > 1e-12:
                        stats["rounding_mismatches"] += 1
                if actual != target:
                    stats["value_mismatches"] += 1
                    if len(stats["examples"]) < 10:
                        stats["examples"].append({"cell": cell.coordinate, "actual": actual, "expected": target})
                if cell.number_format != "0.0000":
                    stats["number_format_mismatches"] += 1
            for cell in row:
                if cell.data_type in ("f", "e"):
                    stats["formula_or_error_cells"] += 1
        stats["first_data_row"] = first_row
        stats["last_data_row"] = last_row
        stats["pass"] = stats["shape_matches"] and stats["header_matches_expanded_template"] and all(
            stats[k] == 0 for k in ("value_mismatches", "time_mismatches", "number_format_mismatches", "non_numeric_data_cells", "formula_or_error_cells", "rounding_mismatches")
        )
        item["sheets"][sheet.title] = stats
    book.close()
    template.close()
    item["files_unchanged_during_audit"] = hashes_before == {"workbook": sha(path), "fields": sha(fields_path), "template": sha(template_path)}
    item["pass"] = all((item["sheet_names_match_template"], source_schedule_ok, grid_ok, item["files_unchanged_during_audit"])) and all(s["pass"] for s in item["sheets"].values())
    audit["workbooks"].append(item)
    print(f"result{q}: {'PASS' if item['pass'] else 'FAIL'}; time={dt}..{end}; cells={sum(s['data_cells_compared'] for s in item['sheets'].values())}", flush=True)

field_checks = {}
for q, a in archives.items():
    c = a["moisture"]
    field_checks[f"q{q}"] = {
        "all_temperature_and_moisture_finite": bool(np.isfinite(a["temperature_c"]).all() and np.isfinite(c).all()),
        "stored_moisture_bounds": [float(c.min()), float(c.max())],
        "radial_monotonicity_violation_max": float(max(0, np.diff(c, axis=1).max())),
        "all_stored_profiles_center_is_max_within_2e_9": bool(np.all(c.max(axis=1) - c[:, 0] <= 2e-9)),
        "stored_time_interval_s": np.unique(np.diff(a["times_s"])).tolist(),
        "stored_grid_nodes": c.shape[1],
    }

q2, q3, q4 = archives[2], archives[3], archives[4]
shared_index = np.searchsorted(q2["times_s"], q3["times_s"])
audit["q2_q3_shared_trajectory"] = {
    key: {"max_abs_difference": float(np.max(np.abs(q2[key][shared_index] - q3[key]))), "exactly_equal": bool(np.array_equal(q2[key][shared_index], q3[key]))}
    for key in ("temperature_c", "moisture")
}

events = {}
for q in (3, 4):
    a = archives[q]
    td = summaries[q]["drying_time_s"]
    maxima = a["moisture"].max(axis=1)
    first = int(np.flatnonzero(maxima < .15)[0])
    ev = {
        "reported_crossing_s": td,
        "reported_crossing_h": td / 3600,
        "first_stored_sample_strictly_below_threshold_s": float(a["times_s"][first]),
        "previous_stored_sample_s": float(a["times_s"][first - 1]),
        "previous_stored_max_moisture": float(maxima[first - 1]),
        "first_below_stored_max_moisture": float(maxima[first]),
        "all_prior_stored_samples_have_somewhere_above_threshold": bool(np.all(maxima[:first] > .15)),
        "threshold_profile_max": float(a["threshold_moisture"].max()),
        "threshold_profile_max_equals_0_15_within_1e_12": bool(abs(a["threshold_moisture"].max() - .15) <= 1e-12),
        "reported_event_within_stored_bracket": bool(a["times_s"][first - 1] < td < a["times_s"][first]),
        "export_end_is_first_minute_at_or_after_event": bool(a["times_s"][-1] == math.ceil(td / 60) * 60),
        "rounding_note": "Threshold uses unrounded values. Four-decimal 0.1500 does not distinguish exactly equal from slightly below.",
    }
    if q == 3:
        max_second = q2["moisture"].max(axis=1)
        j = int(np.flatnonzero(max_second < .15)[0])
        fraction = (max_second[j-1] - .15) / (max_second[j-1] - max_second[j])
        reconstructed_t = float(q2["times_s"][j-1] + fraction * (q2["times_s"][j] - q2["times_s"][j-1]))
        reconstructed_profile = (1-fraction) * q2["moisture"][j-1] + fraction*q2["moisture"][j]
        ev["independent_1s_bracket"] = {
            "before_s": float(q2["times_s"][j-1]), "after_s": float(q2["times_s"][j]),
            "before_max": float(max_second[j-1]), "after_max": float(max_second[j]),
            "reconstructed_crossing_s": reconstructed_t,
            "reported_time_abs_difference_s": abs(reconstructed_t-td),
            "threshold_profile_max_abs_difference": float(np.max(np.abs(reconstructed_profile-a["threshold_moisture"]))),
            "all_prior_second_samples_above": bool(np.all(max_second[:j] > .15)),
        }
    else:
        ev["independent_1s_bracket"] = "Not stored in existing q4 fields (60 s sampling); checked 60 s bracket and saved native-grid threshold profile. Fresh solver rerun is a separate audit."
        ev["radius_at_export_end_cm"] = float(a["radii_m"][-1]*100)
        ev["radii_are_nonincreasing"] = bool(np.all(np.diff(a["radii_m"]) <= 1e-12))
    events[f"q{q}"] = ev

audit["field_checks"] = field_checks
audit["threshold_checks"] = events
audit["limitations"] = [
    "Q2 range is 3 h as explicitly confirmed by the user; longer stored q2 trajectory is not required in result2.xlsx.",
    "Results are conditional model predictions; this audit checks files and stored numerical outputs, not experimental/physical validity.",
    "Q4 outside-radius blanks are an explicit export convention (outside material, not zero or missing computation); final column uses current radius surface.",
    "The continuous threshold crossing is reported at max(C)=0.15; strict below holds immediately after crossing and at the final minute sample. Four-decimal rounding can display 0.1500 even when the underlying value is below.",
    "Q3 stored fixed-grid outputs have 21 radial positions; Q4 stores all 161 native radial nodes. This workbook audit does not independently reconstruct unarchived internal solver states.",
    "Q3/Q4 long-time predictions depend on constant continuation of environmental input after 4 h and the paper's heat/mass and shrinkage assumptions.",
]
audit["workbook_export_pass"] = all(w["pass"] for w in audit["workbooks"])
audit["status"] = "PASS" if audit["workbook_export_pass"] else "FAIL"
(REPORT / "workbook_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
print("AUDIT", audit["status"], REPORT / "workbook_audit.json", flush=True)
