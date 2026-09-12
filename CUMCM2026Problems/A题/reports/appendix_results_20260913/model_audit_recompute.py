"""Read canonical solver/results; recompute only into this report directory."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[1]
CANONICAL = PROJECT / "results"
OUTPUT = BASE / "recomputed"
SOURCE = PROJECT / "code" / "solve_drying.py"
assert OUTPUT.resolve().is_relative_to(BASE.resolve())
assert OUTPUT.resolve() != CANONICAL.resolve()
START = time.perf_counter()
RESUME = "--resume" in sys.argv


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def progress(event, **detail):
    payload = {"event": event, "utc": datetime.now(timezone.utc).isoformat(),
               "elapsed_s": time.perf_counter() - START, **detail}
    write_json(BASE / "model_audit_progress.json", payload)
    with (BASE / "model_audit_progress.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest()


protected = [SOURCE, PROJECT / "附件" / "附件1.xlsx", PROJECT / "附件" / "附件2.xlsx"]
for question in ("q1", "q2", "q3", "q4"):
    protected += [CANONICAL / question / "fields.npz", CANONICAL / question / "summary.json"]
protected += [CANONICAL / "q4" / "fixed_radius_counterfactual.npz"]
before_hashes = (json.loads((BASE / "model_audit_provenance_before.json").read_text(encoding="utf-8"))
                 if RESUME else {str(path.relative_to(PROJECT)): sha256(path) for path in protected if path.exists()})
write_json(BASE / "model_audit_provenance_before.json", before_hashes)
spec = importlib.util.spec_from_file_location("canonical_drying_audit", SOURCE)
solver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = solver
spec.loader.exec_module(solver)
solver.RESULTS_DIR = OUTPUT
OUTPUT.mkdir(parents=True, exist_ok=True)

active = {}
calls = []
brackets = []
if RESUME:
    history = [json.loads(line) for line in (BASE / "model_audit_progress.jsonl").read_text(encoding="utf-8").splitlines()]
    calls = [{key: value for key, value in row.items() if key not in ("event", "utc")}
             for row in history if row["event"] == "simulation_completed"]
    brackets = json.loads((BASE / "model_audit_event_brackets.json").read_text(encoding="utf-8"))
    assert len(calls) == 6, "Resume expects six completed simulations; inspect state before proceeding."
    assert not (OUTPUT / "q4" / "fixed_radius_counterfactual.npz").exists(), "Counterfactual already exists; do not rerun."
original_advance = solver.advance_coupled
original_fixed = solver.simulate_fixed
original_moving = solver.simulate_moving


def audited_advance(*args, **kwargs):
    old_c = args[1]
    dt = float(args[2])
    result = original_advance(*args, **kwargs)
    previous_time = active["simulated_s"]
    active["simulated_s"] += dt
    active["steps"] += 1
    old_max = float(np.max(old_c))
    new_max = float(np.max(result[1]))
    if old_max > solver.THRESHOLD_C >= new_max and not active["bracket_recorded"]:
        weight = (old_max - solver.THRESHOLD_C) / (old_max - new_max)
        threshold_c = old_c + weight * (result[1] - old_c)
        entry = {"simulation": active["simulation"], "before_time_s": previous_time,
                 "after_time_s": active["simulated_s"], "dt_s": dt,
                 "before_max_c": old_max, "after_max_c": new_max,
                 "interpolation_weight": weight,
                 "threshold_time_s": previous_time + weight * dt,
                 "threshold_max_c": float(np.max(threshold_c)),
                 "threshold_center_c": float(threshold_c[0]),
                 "threshold_surface_c": float(threshold_c[-1]),
                 "all_prior_step_maxima_above_threshold": active["prior_above"],
                 "native_node_count": len(old_c)}
        np.savez_compressed(OUTPUT / (active["simulation"] + "_event_bracket.npz"),
                            before_c=old_c, after_c=result[1], threshold_c=threshold_c)
        brackets.append(entry)
        active["bracket_recorded"] = True
        write_json(BASE / "model_audit_event_brackets.json", brackets)
        progress("threshold_bracket", **entry)
    if not active["bracket_recorded"]:
        active["prior_above"] = active["prior_above"] and new_max > solver.THRESHOLD_C
    if active["steps"] % 20000 == 0:
        progress("simulation_progress", simulation=active["simulation"], steps=active["steps"],
                 simulated_s=active["simulated_s"], center_c=float(result[1][0]))
    return result


def wrap_simulation(function, moving):
    def wrapped(*args, **kwargs):
        label = ("moving" if moving else args[1].__name__) + "_" + str(len(calls) + 1)
        active.clear()
        active.update(simulation=label, simulated_s=0.0, steps=0, bracket_recorded=False, prior_above=True)
        call = {"simulation": label, "dt_s": kwargs.get("dt_s"),
                "output_interval_s": kwargs.get("output_interval_s"),
                "include_advection": kwargs.get("include_advection", False)}
        calls.append(call)
        progress("simulation_started", **call)
        started = time.perf_counter()
        value = function(*args, **kwargs)
        threshold = float(value["threshold_time_s"])
        call.update(elapsed_s=time.perf_counter() - started, steps=active["steps"],
                    last_time_s=value["last_time_s"], threshold_time_s=threshold if math.isfinite(threshold) else None,
                    monotone_profiles=value["monotone_profiles"], center_is_max=value["center_is_max"],
                    picard_max=value["picard_max"], picard_mean=value["picard_mean"])
        progress("simulation_completed", **call)
        return value
    return wrapped


solver.advance_coupled = audited_advance
solver.simulate_fixed = wrap_simulation(original_fixed, False)
solver.simulate_moving = wrap_simulation(original_moving, True)
progress("started", python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
         platform=platform.platform(), output=str(OUTPUT), source_sha256=sha256(SOURCE))
if not RESUME:
    solver.run_all(run_convergence=True)
else:
    progress("resumed_only_incomplete_counterfactual", reused_completed_simulations=len(calls))
q4_fixed = solver.simulate_fixed(solver.load_environment(), solver.property_q4,
    end_time_s=None, dt_s=1.0, output_interval_s=60.0, stop_at_threshold=True)
solver.save_npz(OUTPUT / "q4" / "fixed_radius_counterfactual.npz", q4_fixed)
q4_summary = json.loads((OUTPUT / "q4" / "summary.json").read_text(encoding="utf-8"))
fixed_h = float(q4_fixed["threshold_time_s"]) / 3600.0
moving_h = q4_summary["drying_time_h"]
q4_summary["fixed_radius_counterfactual"] = {
    "same_appendix4_properties_time_h": fixed_h, "moving_radius_time_h": moving_h,
    "time_reduction_h": fixed_h - moving_h, "relative_reduction": (fixed_h - moving_h) / fixed_h}
solver.write_summary(OUTPUT / "q4" / "summary.json", q4_summary)


def compare_npz(reference, recomputed):
    with np.load(reference, allow_pickle=False) as old, np.load(recomputed, allow_pickle=False) as new:
        result = {"same_keys": set(old.files) == set(new.files), "reference_keys": old.files,
                  "recomputed_keys": new.files, "arrays": {}}
        for key in sorted(set(old.files) & set(new.files)):
            left, right = old[key], new[key]
            item = {"shape": list(left.shape), "recomputed_shape": list(right.shape),
                    "dtype": str(left.dtype), "recomputed_dtype": str(right.dtype)}
            if left.shape == right.shape:
                item["exact_equal"] = bool(np.array_equal(left, right, equal_nan=True))
                item["max_absolute_difference"] = float(np.nanmax(np.abs(left - right))) if left.size else 0.0
                item["different_values"] = int(np.count_nonzero(~np.isclose(left, right, rtol=0, atol=0, equal_nan=True)))
            else:
                item["exact_equal"] = False
            result["arrays"][key] = item
        result["all_exact_equal"] = result["same_keys"] and all(x["exact_equal"] for x in result["arrays"].values())
        return result


def json_differences(left, right, path=""):
    if isinstance(left, dict) and isinstance(right, dict):
        findings = []
        for key in sorted(set(left) | set(right)):
            child = path + "/" + key
            if key not in left or key not in right:
                findings.append({"path": child, "reference": left.get(key), "recomputed": right.get(key), "missing_key": True})
            else:
                findings.extend(json_differences(left[key], right[key], child))
        return findings
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [{"path": path, "reference_length": len(left), "recomputed_length": len(right)}]
        return [entry for i, (a, b) in enumerate(zip(left, right)) for entry in json_differences(a, b, path + "/" + str(i))]
    if left == right:
        return []
    entry = {"path": path, "reference": left, "recomputed": right}
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        entry["absolute_difference"] = abs(left - right)
    return [entry]


comparisons = {}
for question in ("q1", "q2", "q3", "q4"):
    item = {"fields": compare_npz(CANONICAL / question / "fields.npz", OUTPUT / question / "fields.npz")}
    old_summary = json.loads((CANONICAL / question / "summary.json").read_text(encoding="utf-8"))
    new_summary = json.loads((OUTPUT / question / "summary.json").read_text(encoding="utf-8"))
    item["summary_differences"] = json_differences(old_summary, new_summary)
    item["summary_exact_equal"] = not item["summary_differences"]
    comparisons[question] = item
    progress("comparison", question=question, fields_exact_equal=item["fields"]["all_exact_equal"],
             summary_exact_equal=item["summary_exact_equal"], summary_difference_count=len(item["summary_differences"]))
comparisons["q4_fixed_radius_counterfactual"] = compare_npz(
    CANONICAL / "q4" / "fixed_radius_counterfactual.npz", OUTPUT / "q4" / "fixed_radius_counterfactual.npz")
after_hashes = {str(path.relative_to(PROJECT)): sha256(path) for path in protected if path.exists()}
report = {"scope": "Canonical solver executed anew with isolated output; all stored arrays and all summary fields compared.",
          "resumed_after_interruption": RESUME,
          "q2_workbook_scope": "User requires only 1..10800 s in result2.xlsx; long q2 fields are retained for q3 shared trajectory.",
          "simulation_calls": calls, "event_brackets": brackets, "comparisons": comparisons,
          "protected_hashes_before": before_hashes, "protected_hashes_after": after_hashes,
          "protected_files_unchanged": before_hashes == after_hashes,
          "elapsed_s": time.perf_counter() - START,
          "all_four_fields_exact_equal": all(comparisons[q]["fields"]["all_exact_equal"] for q in ("q1", "q2", "q3", "q4")),
          "all_four_summaries_exact_equal": all(comparisons[q]["summary_exact_equal"] for q in ("q1", "q2", "q3", "q4"))}
write_json(BASE / "model_audit_recompute.json", report)
progress("completed", report=str(BASE / "model_audit_recompute.json"),
         all_four_fields_exact_equal=report["all_four_fields_exact_equal"],
         all_four_summaries_exact_equal=report["all_four_summaries_exact_equal"],
         protected_files_unchanged=report["protected_files_unchanged"])
