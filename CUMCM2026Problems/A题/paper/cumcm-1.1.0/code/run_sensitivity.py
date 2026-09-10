"""Boundary-condition sensitivity for the Q3 and Q4 drying times."""

from __future__ import annotations

import json
import sys

from solve_drying import (
    RESULTS_DIR,
    load_environment,
    load_radius_history,
    property_q23,
    simulate_fixed,
    simulate_moving,
)


SCENARIOS = {
    "temperature_minus_5pct": (0.95, 1.0),
    "temperature_plus_5pct": (1.05, 1.0),
    "ambient_moisture_minus_5pct": (1.0, 0.95),
    "ambient_moisture_plus_5pct": (1.0, 1.05),
}


def run() -> None:
    environment = load_environment()
    radius_history = load_radius_history()
    output: dict[str, dict[str, float]] = {}
    for name, (temperature_scale, moisture_scale) in SCENARIOS.items():
        q3 = simulate_fixed(
            environment,
            property_q23,
            end_time_s=None,
            dt_s=20.0,
            output_interval_s=3600.0,
            stop_at_threshold=True,
            terminal_temp_scale=temperature_scale,
            terminal_moisture_scale=moisture_scale,
        )
        q4 = simulate_moving(
            environment,
            radius_history,
            dt_s=20.0,
            output_interval_s=3600.0,
            stop_at_threshold=True,
            terminal_temp_scale=temperature_scale,
            terminal_moisture_scale=moisture_scale,
        )
        output[name] = {
            "terminal_temperature_scale": temperature_scale,
            "terminal_moisture_scale": moisture_scale,
            "q3_drying_time_h": float(q3["threshold_time_s"]) / 3600.0,
            "q4_drying_time_h": float(q4["threshold_time_s"]) / 3600.0,
        }

    path = RESULTS_DIR / "sensitivity.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run()
