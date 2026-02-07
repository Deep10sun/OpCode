import pandas as pd
import os
import subprocess
import sys
from glob import glob

def run_full_pipeline():
    """Run the complete end-to-end pipeline."""
    print("\n" + "="*80)
    print("RUNNING COMPLETE PIPELINE: Raw Data → Final Corrected Output")
    print("="*80)
    
    result = subprocess.run(
        [sys.executable, "full_pipeline.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    return result.returncode == 0

def load_final_data():
    """Load the final drift-corrected data."""
    aligned_folder = os.path.join(os.path.dirname(__file__), "pre_processing", "aligned")
    final_file = os.path.join(aligned_folder, "merged_by_distance_corrected.csv")
    
    if not os.path.exists(final_file):
        print(f"\nFinal data file not found: {final_file}")
        print("Please run the pipeline first.")
        return None
    
    print(f"\nLoading final drift-corrected data from {final_file}...")
    df = pd.read_csv(final_file)
    return df

# Run the complete pipeline
if __name__ == "__main__":
    if run_full_pipeline():
        # Load and display the final data
        df = load_final_data()
        if df is not None:
            print(f"\nSuccessfully loaded {len(df)} rows of final data")
            print(f"\nColumns: {list(df.columns)}")
            print(f"\nFirst few rows:")
            print(df.head())
    else:
        print("\nPipeline execution failed")
        sys.exit(1)