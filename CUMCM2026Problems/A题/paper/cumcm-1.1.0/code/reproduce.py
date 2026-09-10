"""Sequential reproducibility entrypoint. Excel export is an explicit option."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workbooks',action='store_true',help='Also regenerate the four Excel submissions')
    args=parser.parse_args()
    scripts=['solve_drying.py','run_q4_counterfactual.py','grid_study.py',
             'check_fields.py','check_numerics.py','validate_long.py','sensitivity_study.py',
             'make_figures.py','make_flowcharts.py']
    if args.workbooks:
        scripts.append('write_results.py')
    scripts.extend(['write_revision_report.py','build_paper_data.py'])
    for name in scripts:
        subprocess.run([sys.executable,str(Path(__file__).with_name(name))],check=True)


if __name__=='__main__':
    main()
