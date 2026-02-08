import os
import pandas as pd
import numpy as np

# Paths
ALIGNED_FOLDER = os.path.join(os.path.dirname(__file__), "aligned")
INPUT_FILE = os.path.join(ALIGNED_FOLDER, "merged_by_distance.csv")
OUTPUT_FILE = os.path.join(ALIGNED_FOLDER, "merged_by_distance_corrected.csv")


def _linear_extrapolate(x, x0, y0, x1, y1):
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _build_drift_function(x_2007, x_2015):
    """Return a callable Δ(x) using piecewise-linear interpolation/extrapolation."""
    x = np.asarray(x_2007, dtype="float64")
    y = np.asarray(x_2015, dtype="float64")
    delta = y - x

    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    delta_sorted = delta[sort_idx]

    def drift_fn(x_query):
        xq = np.asarray(x_query, dtype="float64")
        delta_interp = np.interp(xq, x_sorted, delta_sorted)

        if len(x_sorted) >= 2:
            left_mask = xq < x_sorted[0]
            right_mask = xq > x_sorted[-1]

            if np.any(left_mask):
                delta_interp[left_mask] = _linear_extrapolate(
                    xq[left_mask],
                    x_sorted[0],
                    delta_sorted[0],
                    x_sorted[1],
                    delta_sorted[1],
                )

            if np.any(right_mask):
                delta_interp[right_mask] = _linear_extrapolate(
                    xq[right_mask],
                    x_sorted[-2],
                    delta_sorted[-2],
                    x_sorted[-1],
                    delta_sorted[-1],
                )

        return delta_interp

    return drift_fn


def _apply_coordinate_transform(x_values, drift_fn):
    """Apply T(x) = x - Δ(x)."""
    return np.asarray(x_values, dtype="float64") - drift_fn(x_values)


def main():
    print(f"Loading merged data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Find the raw distance columns preserved in the merge
    raw_dist_cols = [col for col in df.columns if '__distance' in col]
    print(f"\nFound raw distance columns: {raw_dist_cols}")
    
    if not raw_dist_cols or len(raw_dist_cols) < 2:
        print("ERROR: Could not find raw distance columns.")
        print("Please re-run align.py to ensure raw distances are preserved.")
        return
    
    # Get r_2007 and r_2015 raw distances
    dist_2007_col = next((col for col in raw_dist_cols if '2007' in col), None)
    dist_2015_col = next((col for col in raw_dist_cols if '2015' in col), None)
    
    if not dist_2007_col or not dist_2015_col:
        print(f"ERROR: Could not find both 2007 and 2015 distance columns")
        print(f"Available: {raw_dist_cols}")
        return
    
    print(f"Using {dist_2007_col} and {dist_2015_col} to build drift function")
    
    # Build drift function from raw distances
    x_2007 = pd.to_numeric(df[dist_2007_col], errors="coerce").values
    x_2015 = pd.to_numeric(df[dist_2015_col], errors="coerce").values
    
    # Remove NaN pairs
    valid_mask = ~(np.isnan(x_2007) | np.isnan(x_2015))
    x_2007_clean = x_2007[valid_mask]
    x_2015_clean = x_2015[valid_mask]
    
    print(f"Building drift function from {len(x_2007_clean)} valid weld pairs")
    drift_fn = _build_drift_function(x_2007_clean, x_2015_clean)
    
    # Apply drift correction to distance_corrected and r_2022 columns
    result_df = df.copy()
    
    # Apply to distance_corrected - replace the column with doubly corrected version
    if 'distance_corrected' in df.columns:
        dist_corrected = pd.to_numeric(df['distance_corrected'], errors="coerce").values
        distance_doubly_corrected = _apply_coordinate_transform(dist_corrected, drift_fn)
        result_df['distance_corrected'] = distance_doubly_corrected
        print(f"\nApplied drift correction to distance_corrected (replacing original)")
    
    # Apply to r_2022 distance if present
    if 'distance_2022' in df.columns:
        dist_2022 = pd.to_numeric(df['distance_2022'], errors="coerce").values
        distance_2022_corrected = _apply_coordinate_transform(dist_2022, drift_fn)
        result_df['distance_2022_corrected'] = distance_2022_corrected
        print(f"Applied drift correction to distance_2022")
    
    # Add run_id column set to 0
    result_df['run_id'] = 0

    # Drop requested columns from final output (ignore if missing)
    columns_to_drop = [
        "r_2007_weld_aligned__distance",
        "r_2015_weld_aligned__distance",
        "distance__delta",
        "thickness__avg",
        "thickness__delta",
        "thickness___delta",
        "jlength__avg",
        "jlength__delta",
        "jlength___delta",
        "distance_2022",
        "distance_2022_corrected",
        "thickness_2022",
    ]
    result_df = result_df.drop(columns=columns_to_drop, errors="ignore")
    result_df["type"] = "weld"
    # Save output
    result_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved corrected data to {OUTPUT_FILE}")
    
    # Print summary
    print("\n" + "="*70)
    print("DRIFT CORRECTION SUMMARY")
    print("="*70)
    if 'distance_corrected' in result_df.columns:
        print(f"distance_corrected (doubly corrected):")
        print(f"  Min: {result_df['distance_corrected'].min():.4f} ft")
        print(f"  Max: {result_df['distance_corrected'].max():.4f} ft")
        print(f"  Mean: {result_df['distance_corrected'].mean():.4f} ft")
    
    if 'distance_2022_corrected' in result_df.columns:
        print(f"\ndistance_2022_corrected:")
        print(f"  Min: {result_df['distance_2022_corrected'].min():.4f} ft")
        print(f"  Max: {result_df['distance_2022_corrected'].max():.4f} ft")
        print(f"  Mean: {result_df['distance_2022_corrected'].mean():.4f} ft")
    
    print("="*70)
    print("\nFirst 5 rows:")
    display_cols = ['id', 'distance_corrected', 'distance_2022_corrected'] if 'distance_2022_corrected' in result_df.columns else ['id', 'distance_corrected']
    print(result_df[display_cols].head())


if __name__ == "__main__":
    main()