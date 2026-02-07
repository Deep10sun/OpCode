import os
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# Paths
ALIGNED_FOLDER = os.path.join(os.path.dirname(__file__), "aligned")
CORRECTED_FOLDER = os.path.join(os.path.dirname(__file__), "corrected")
os.makedirs(CORRECTED_FOLDER, exist_ok=True)

INPUT_FILE = os.path.join(ALIGNED_FOLDER, "merged_by_distance.csv")
OUTPUT_FILE = os.path.join(CORRECTED_FOLDER, "drift_corrected.csv")
PLOT_FILE = os.path.join(CORRECTED_FOLDER, "drift_function.png")


def build_drift_function(df):
    """
    Build a piecewise-linear drift function Δ(x) from weld pairs.
    
    Δ(x) = x_2015 - x_2007 (the distance discrepancy at each weld location)
    
    Args:
        df: DataFrame with columns 'r_2007_weld_aligned__distance' and 'r_2015_weld_aligned__distance'
    
    Returns:
        drift_function: A callable function Δ(x) that interpolates drift at any distance x
        x_points: Array of x-coordinates (2007 distances)
        delta_values: Array of drift values at each point
    """
    x_2007 = df['r_2007_weld_aligned__distance'].values
    x_2015 = df['r_2015_weld_aligned__distance'].values
    
    # Calculate drift: Δ(x) = x_2015 - x_2007
    delta_values = x_2015 - x_2007
    
    # Sort by 2007 distances to ensure monotonic x-axis
    sort_idx = np.argsort(x_2007)
    x_points = x_2007[sort_idx]
    delta_sorted = delta_values[sort_idx]
    
    # Build piecewise-linear interpolation
    # Using linear interpolation between weld points
    drift_function = interp1d(
        x_points, 
        delta_sorted, 
        kind='linear', 
        fill_value='extrapolate',
        assume_sorted=True
    )
    
    return drift_function, x_points, delta_sorted


def coordinate_transform(x_2007, drift_function):
    """
    Apply coordinate transform: T(x) = x - Δ(x)
    
    This corrects 2007 distances using the drift function to align with 2015 coordinate system.
    
    Args:
        x_2007: Array of 2007 distances
        drift_function: Callable drift function Δ(x)
    
    Returns:
        x_corrected: Corrected distances aligned to 2015 system
    """
    drift = drift_function(x_2007)
    x_corrected = x_2007 - drift
    return x_corrected


def plot_drift_function(x_points, delta_values, output_path):
    """Plot the drift function for visualization."""
    plt.figure(figsize=(12, 6))
    
    # Plot scatter of weld points
    plt.scatter(x_points, delta_values, color='red', s=50, label='Weld pair observations', zorder=3)
    
    # Plot fitted line
    x_continuous = np.linspace(x_points.min(), x_points.max(), 1000)
    drift_func_temp = interp1d(x_points, delta_values, kind='linear', assume_sorted=True)
    delta_continuous = drift_func_temp(x_continuous)
    plt.plot(x_continuous, delta_continuous, 'b-', linewidth=2, label='Piecewise-linear drift Δ(x)')
    
    plt.xlabel('Distance 2007 (ft)', fontsize=12)
    plt.ylabel('Drift Δ(x) = x_2015 - x_2007 (ft)', fontsize=12)
    plt.title('Piecewise-Linear Drift Function', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Saved drift function plot to {output_path}")
    plt.close()


def main():
    # Load merged data
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # Build drift function
    print("Building piecewise-linear drift function Δ(x)...")
    drift_func, x_points, delta_values = build_drift_function(df)
    
    # Apply coordinate transform
    print("Applying coordinate transform T(x) = x - Δ(x)...")
    x_2007 = df['r_2007_weld_aligned__distance'].values
    x_corrected = coordinate_transform(x_2007, drift_func)
    
    # Create output dataframe
    result_df = df.copy()
    result_df['x_2007_original'] = x_2007
    result_df['drift_delta'] = drift_func(x_2007)
    result_df['x_2007_corrected'] = x_corrected
    
    # Reorder columns for clarity
    cols = ['id', 'x_2007_original', 'drift_delta', 'x_2007_corrected', 
            'r_2015_weld_aligned__distance', 'thickness__avg', 'thickness__delta',
            'jlength__avg', 'jlength__delta']
    result_df = result_df[cols]
    
    # Save corrected data
    result_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved drift-corrected data to {OUTPUT_FILE}")
    
    # Plot drift function
    plot_drift_function(x_points, delta_values, PLOT_FILE)
    
    # Print summary statistics
    print("\n" + "="*70)
    print("DRIFT CORRECTION SUMMARY")
    print("="*70)
    print(f"Number of weld pairs: {len(df)}")
    print(f"Distance range (2007): {x_2007.min():.2f} - {x_2007.max():.2f} ft")
    print(f"Drift range: {delta_values.min():.4f} - {delta_values.max():.4f} ft")
    print(f"Mean drift: {delta_values.mean():.4f} ft")
    print(f"Std drift: {delta_values.std():.4f} ft")
    print(f"\nMax correction applied: {np.abs(x_2007 - x_corrected).max():.4f} ft")
    print(f"Mean correction: {np.abs(x_2007 - x_corrected).mean():.4f} ft")
    print("="*70)
    
    # Print sample rows
    print("\nSample corrected data (first 5 rows):")
    print(result_df.head())


if __name__ == "__main__":
    main()
