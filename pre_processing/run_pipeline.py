#!/usr/bin/env python3
"""
Complete pipeline runner: extract welds -> merge/align -> apply drift correction
"""
import subprocess
import sys
import os

def run_step(script_name, description):
    """Run a pipeline step and report results."""
    print(f"\n{'='*70}")
    print(f"STEP: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=os.path.dirname(__file__),
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"\nERROR in {script_name}")
        return False
    
    print(f"\n{description} completed successfully")
    return True

def main():
    steps = [
        ("data_preprocessing.py", "Preprocess raw data (remove NaN columns/rows)"),
        ("extract.py", "Extract weld events from r_2007, r_2015, r_2022"),
        ("align.py", "Merge and align welds by distance with drift correction"),
        ("apply_drift_correction.py", "Apply drift correction to distance columns"),
        ("normalize_names.py", "Normalize columns across runs"),
    ]
    
    for script, description in steps:
        if not run_step(script, description):
            print(f"\n  Pipeline stopped at: {description}")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
