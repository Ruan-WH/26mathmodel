# File: code/check_moving_mesh_delivery.py
"""Verify saved Q4 results and the paper without integrating or packaging by default.

Example: python check_moving_mesh_delivery.py --log ../paper/cumcm-1.1.0/build/main.log
Use --report to choose the JSON destination, and --package only to copy main.pdf
to the submission filename. Historical protection hashes are provenance, not a
baseline for a later revision; this run separately checks before/after hashes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import numpy as np
import pymupdf
from solve_drying import INITIAL_C, THRESHOLD_C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/q4/validation_moving_mesh"
PAPER = ROOT / "paper/cumcm-1.1.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf8"))


def git_output(*args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), *args], stderr=subprocess.DEVNULL,
            text=True, encoding="utf8").strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def snapshot(report_path):
    """Protect calculation code, supplied inputs and all saved numerical results."""
    files = set((ROOT / "code").glob("*.py"))
    files.update((ROOT / "paper").rglob("*.py"))
    files.update(path for path in (ROOT / "附件").rglob("*") if path.is_file())
    files.update(ROOT.rglob("*.xlsx"))
    for pattern in ("*.npz", "*.json", "*.csv"):
        files.update((ROOT / "results").rglob(pattern))
    return {path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted(files) if path.resolve() != report_path}


def check_arrays(arrays, summary, reference, official):
    """Check dimensions against coordinates and official Q4 data, not old lengths."""
    for name, values in arrays.items():
        require(np.isfinite(values).all(), f"Nonfinite validation array: {name}")
    for name, values in reference.items():
        require(np.isfinite(values).all(), f"Nonfinite official Q4 array: {name}")
    times, xi, trace = arrays["times_s"], arrays["xi"], arrays["step_trace"]
    require(times.ndim == xi.ndim == 1 and len(times) > 1 and len(xi) > 1,
            "Time and node coordinates must be nonempty vectors")
    require(np.array_equal(times, reference["times_s"]), "Q4 output times differ")
    require(np.all(np.diff(times) > 0) and times[0] == 0, "Invalid output time axis")
    sample_dt = float(times[1] - times[0])
    require(np.allclose(np.diff(times), sample_dt, rtol=0, atol=1e-8),
            "Irregular field output sampling")
    require(np.all(np.diff(xi) > 0) and xi[0] == 0 and xi[-1] == 1,
            "Invalid normalized radial grid")
    require(len(xi) == summary["nodes"] == official["numerics"]["nodes"],
            "Node coordinates disagree with solver metadata")
    require(len(reference["xi"]) == official["numerics"]["output_nodes"],
            "Official Q4 output-node metadata differs")
    require(times[-1] == official["output_end_s"], "Q4 output end time differs")
    require(arrays["radii_m"].shape == times.shape and
            np.array_equal(arrays["radii_m"], reference["radii_m"]) and
            np.all(arrays["radii_m"] > 0), "Radius history differs")
    shape = (len(times), len(xi))
    for name in ("mapping_moisture", "moving_moisture",
                 "mapping_temperature", "moving_temperature"):
        require(arrays[name].shape == shape, f"Wrong field shape: {name}")
    for name in ("mapping_moisture", "moving_moisture"):
        values = arrays[name]
        require(values.min() >= -1e-10 and values.max() <= INITIAL_C + 1e-8,
                f"Moisture outside physical bounds: {name}")
        require(np.max(np.diff(values, axis=1)) <= 2e-9,
                f"Nonmonotone radial moisture profile: {name}")
    require(summary["monotone_profiles"], "Full-step monotonicity check failed")
    require(trace.shape == (summary["time_steps"] + 1, 8), "Trace metadata differs")
    dt = float(summary["dt_s"])
    require(dt > 0 and dt == official["numerics"]["dt_s"], "Q4 time steps differ")
    require(trace[0, 0] == 0 and trace[-1, 0] == times[-1], "Trace endpoints differ")
    increments = np.diff(trace[:, 0])
    require(np.all(increments > 0) and np.all(increments <= dt + 1e-8),
            "Missing, duplicate, or oversized integration steps")
    short = np.flatnonzero(increments < dt - 1e-8) + 1
    require(np.all(np.isclose(np.remainder(trace[short, 0], sample_dt), 0, atol=1e-8)),
            "Short steps must end at field-output times")
    indices = np.searchsorted(trace[:, 0], times)
    require(np.array_equal(trace[indices, 0], times), "Field times missing from trace")
    for name, node, column in (("mapping_moisture", 0, 1), ("moving_moisture", 0, 2),
                               ("mapping_moisture", -1, 3), ("moving_moisture", -1, 4)):
        require(np.allclose(arrays[name][:, node], trace[indices, column], rtol=0, atol=1e-12),
                f"Field and step trace disagree: {name}, node {node}")
    require(np.all(trace[:, 5:] >= 0), "Negative absolute errors in step trace")
    require(np.allclose(abs(trace[:, 1] - trace[:, 2]), trace[:, 7], rtol=0, atol=1e-14),
            "Center-error column is inconsistent")
    for field, column, tolerance in (("moisture", 5, 1e-14), ("temperature", 6, 1e-12)):
        errors = np.max(abs(arrays[f"mapping_{field}"] - arrays[f"moving_{field}"]), axis=1)
        require(np.allclose(errors, trace[indices, column], rtol=0, atol=tolerance),
                f"Full-field {field} errors disagree with trace")
    error_limits = {"max_abs_moisture_field_difference": (5, 1e-9),
                    "max_abs_temperature_field_difference": (6, 1e-7),
                    "max_abs_center_moisture_difference": (7, 1e-9)}
    for name, (column, limit) in error_limits.items():
        value = float(trace[:, column].max())
        require(summary[name] == value and value < limit, f"Error check failed: {name}")
    for name, column in (("mapping", 1), ("moving_mesh", 2)):
        event = summary["events"][name]
        moisture = arrays[f"{name}_event_moisture"]
        temperature = arrays[f"{name}_event_temperature"]
        require(moisture.shape == temperature.shape == xi.shape, "Wrong event field shape")
        require(abs(moisture.max() - THRESHOLD_C) < 1e-10, "Event misses drying threshold")
        crossings = np.flatnonzero(trace[:, column] <= THRESHOLD_C)
        require(len(crossings) > 0 and crossings[0] > 0, "Threshold crossing missing")
        i = crossings[0]
        fraction = ((trace[i-1, column] - THRESHOLD_C) /
                    (trace[i-1, column] - trace[i, column]))
        crossing_time = trace[i-1, 0] + fraction * (trace[i, 0] - trace[i-1, 0])
        require(abs(crossing_time - event["time_s"]) < 1e-6, "Event time differs from trace")
        require(abs(event["time_s"] / 3600 - event["time_h"]) < 1e-12, "Event time units differ")
    delta = abs(summary["events"]["mapping"]["time_s"] -
                summary["events"]["moving_mesh"]["time_s"])
    require(delta == summary["drying_time_abs_difference_s"] and delta < 1e-5,
            "Independent drying-time error exceeds tolerance")
    require(np.isclose(summary["drying_time_relative_difference"],
                       delta / summary["events"]["mapping"]["time_s"], rtol=1e-12, atol=1e-18),
            "Relative drying-time error is inconsistent")
    reproduction = {}
    for field, key, limit in (("moisture", "moisture", 1e-12),
                              ("temperature", "temperature_c", 1e-10)):
        expected = np.array([np.interp(reference["xi"], xi, row)
                             for row in arrays[f"mapping_{field}"]])
        require(reference[key].shape == expected.shape, f"Official {field} field shape differs")
        difference = float(np.max(abs(expected - reference[key])))
        require(difference < limit, f"Saved validation no longer reproduces official {field}")
        reproduction[f"max_{field}_difference"] = difference
    time_difference = abs(summary["events"]["mapping"]["time_s"] - official["drying_time_s"])
    require(time_difference < 1e-6, "Official drying time differs")
    reproduction["drying_time_difference_s"] = time_difference
    return dict(field_shape=list(shape), step_trace_shape=list(trace.shape),
                output_end_s=float(times[-1]), field_sampling_s=sample_dt, dt_s=dt,
                error_limits={name: limit for name, (_, limit) in error_limits.items()},
                reference_reproduction=reproduction)


def check_paper(log_path, skip_build_check):
    pdf = PAPER / "main.pdf"
    with pymupdf.open(pdf) as doc:
        result = dict(pdf_pages=len(doc), paper_sha256=sha256(pdf), validation_pages=[
            i + 1 for i, page in enumerate(doc) if any(term in page.get_text() for term in
            ("移动网格独立验证", "移动网格与固定域映射的数值比较", "两种坐标实现的中心"))])
    if skip_build_check:
        result["build_check"] = {"status": "not_verified", "reason": "Explicit --skip-build-check"}
        return result
    if log_path is None:
        candidates = [PAPER / "build/main.log", PAPER / "main.log"]
        available = [path for path in candidates if path.is_file()]
        require(available, "No build log: supply --log, or explicitly use --skip-build-check")
        log_path = max(available, key=lambda path: path.stat().st_mtime)
    require(log_path.is_file(), f"Build log missing: {log_path}")
    log = log_path.read_text(encoding="utf8", errors="replace")
    bad = [item for item in ("Overfull", "undefined references", "Missing character:",
                             "Float too large", "! LaTeX Error", "Emergency stop") if item in log]
    require(not bad, f"LaTeX warnings/errors require review: {bad}")
    completed = re.findall(r"Output written on .*?\((\d+) pages?", log, flags=re.DOTALL)
    require(completed and int(completed[-1]) == result["pdf_pages"],
            "Log has no successful TeX output with the current PDF page count")
    require(log_path.stat().st_mtime >= pdf.stat().st_mtime - 120,
            "Build log predates current PDF; supply the current compilation log")
    result["build_check"] = dict(status="passed", log_path=str(log_path.resolve()),
                                 log_sha256=sha256(log_path), warnings_or_errors=bad)
    return result


def historical_provenance():
    path = OUT / "protected_files_sha256.json"
    if not path.is_file():
        return {"role": "historical_only", "available": False}
    manifest = load_json(path)
    changed = []
    for name, old_hash in manifest.items():
        current = ROOT / name.replace("\\", "/")
        if not current.is_file() or sha256(current) != old_hash:
            changed.append(name)
    return dict(role="historical_only_not_current_acceptance_baseline",
                path=path.relative_to(ROOT).as_posix(), sha256=sha256(path),
                last_recorded_commit=git_output("log", "-1", "--format=%H", "--", str(path)),
                different_from_historical=changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, help="Current TeX log (default: newest paper/build/main.log or paper/main.log)")
    parser.add_argument("--report", type=Path, default=OUT / "delivery_checks.json")
    parser.add_argument("--skip-build-check", action="store_true", help="Check data/PDF only; report will explicitly be partial")
    parser.add_argument("--package", action="store_true", help="Also copy verified main.pdf to A题_完整论文.pdf")
    args = parser.parse_args()
    require(not (args.package and args.skip_build_check), "Packaging requires build-log verification")
    report_path = args.report.resolve()
    require(report_path.suffix.lower() == ".json", "Report must be a JSON file")
    before = snapshot(report_path)
    # A report may replace an earlier delivery report, but never a numerical result or historical manifest.
    if report_path.exists():
        previous = load_json(report_path)
        require("protected_files_unchanged" in previous or previous.get("check_kind") == "q4_delivery",
                "Refusing to overwrite a file that is not a delivery-check report")
    with np.load(OUT / "fields.npz", allow_pickle=False) as saved, \
            np.load(ROOT / "results/q4/fields.npz", allow_pickle=False) as formal:
        arrays = {name: saved[name] for name in saved.files}
        reference = {name: formal[name] for name in formal.files}
    result = dict(check_kind="q4_delivery", schema_version=2,
                  checked_at_utc=datetime.now(timezone.utc).isoformat(), git_head=git_output("rev-parse", "HEAD"),
                  numerical_checks=check_arrays(arrays, load_json(OUT / "summary.json"), reference,
                                                load_json(ROOT / "results/q4/summary.json")),
                  historical_manifest=historical_provenance(),
                  **check_paper(args.log, args.skip_build_check))
    if args.package:
        destination = ROOT / "A题_完整论文.pdf"
        shutil.copy2(PAPER / "main.pdf", destination)
        result["packaged_pdf"] = dict(path=str(destination), sha256=sha256(destination))
    after = snapshot(report_path)
    require(before == after, "Protected calculation/input/result files changed during this check")
    result["protection"] = dict(unchanged=True, file_count=len(before), before_sha256=before, after_sha256=after)
    result["status"] = "partial_build_not_verified" if args.skip_build_check else "passed"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({key: result[key] for key in ("status", "numerical_checks", "pdf_pages", "build_check")},
                     ensure_ascii=False, indent=2))
    print(f"Report: {report_path}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(f"Delivery check failed: {error}", file=sys.stderr)
        sys.exit(1)
