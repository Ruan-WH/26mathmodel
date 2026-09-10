"""Counterfactual Q4 run using Appendix-4 properties but a fixed radius."""

from __future__ import annotations

import json
import sys

from solve_drying import (
    RESULTS_DIR,
    load_environment,
    property_q4,
    save_npz,
    simulate_fixed,
)


def main() -> None:
    environment = load_environment()
    simulation = simulate_fixed(
        environment,
        property_q4,
        end_time_s=None,
        dt_s=10.0,
        output_interval_s=60.0,
        stop_at_threshold=True,
    )
    save_npz(RESULTS_DIR / "q4" / "fixed_radius_counterfactual.npz", simulation)
    summary_path = RESULTS_DIR / "q4" / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    fixed_time_h = float(simulation["threshold_time_s"]) / 3600.0
    moving_time_h = float(summary["drying_time_h"])
    summary["fixed_radius_counterfactual"] = {
        "same_appendix4_properties_time_h": fixed_time_h,
        "moving_radius_time_h": moving_time_h,
        "time_reduction_h": fixed_time_h - moving_time_h,
        "relative_reduction": (fixed_time_h - moving_time_h) / fixed_time_h,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary["fixed_radius_counterfactual"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
