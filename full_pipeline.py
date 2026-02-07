#!/usr/bin/env python3
"""
Complete end-to-end pipeline: Load raw data -> Preprocess -> Extract -> Align -> Drift Correct
"""
import subprocess
import sys
import os

def run_step(script_name, description, working_dir=None):
    """Run a pipeline step and report results."""
    print(f"\n{'='*70}")
    print(f"STEP: {description}")
    print(f"Script: {script_name}")
    print(f"{'='*70}")
    
    cwd = working_dir if working_dir else os.path.dirname(os.path.abspath(__file__))
    
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=cwd,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"\nERROR in {script_name}")
        return False
    
    print(f"\n{description} completed successfully")
    return True

def main():
    # Get paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root_dir, "data")
    preproc_dir = os.path.join(root_dir, "pre_processing")
    
    steps = [
        ("load_data.py", "Load raw data from Excel and save to CSV", data_dir),
        ("pre_processing/run_pipeline.py", "Run preprocessing and alignment pipeline", root_dir),
    ]
    
    print("\n" + "="*70)
    print("COMPLETE END-TO-END PIPELINE")
    print("Raw Data → Processed → Extracted → Aligned → Drift Corrected")
    print("="*70)
    
    for script, description, working_dir in steps:
        if not run_step(script, description, working_dir):
            print(f"\nPipeline stopped at: {description}")
            return 1
    
    print("\n" + "="*70)
    print("COMPLETE PIPELINE EXECUTED SUCCESSFULLY")
    print("="*70)
    print("\nGenerated files:")
    print("\n  RAW DATA (data/):")
    print("    - r_2007.csv")
    print("    - r_2015.csv")
    print("    - r_2022.csv")
    print("    - summary.csv")
    
    print("\n  PROCESSED DATA (pre_processing/processed/):")
    print("    - r_2007_processed.csv")
    print("    - r_2015_processed.csv")
    print("    - r_2022_processed.csv")
    
    print("\n  EXTRACTED WELDS (pre_processing/extracted/):")
    print("    - r_2007_weld_aligned.csv")
    print("    - r_2015_weld_aligned.csv")
    print("    - r_2022_weld_aligned.csv")
    
    print("\n  ALIGNED & CORRECTED (pre_processing/aligned/):")
    print("    - merged_by_distance.csv")
    print("    - merged_by_distance_corrected.csv (FINAL OUTPUT)")
    
    print("\nFinal output location:")
    print(f"  {os.path.join(preproc_dir, 'aligned', 'merged_by_distance_corrected.csv')}")
    print("\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
