"""Short-duration Q1 validation using the matched-grid axisymmetric solver.

Whole-run extrema and final-time differences are explicitly distinguished.
For the full drying process, run validate_long_2d.py.
"""
import json
import sys
from solve_drying import RESULTS_DIR
from validate_long_2d import run_case


def run():
    report = run_case(1, 41, 21, 10.0)
    report['one_dimensional_midplane_pass'] = (
        report['whole_run_midplane_max_temperature_difference'] < 0.1
        and report['whole_run_midplane_max_moisture_difference'] < 1e-3)
    output = RESULTS_DIR / 'q1' / 'validation_2d.json'
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()
