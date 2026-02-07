import os
from glob import glob
import pandas as pd
import numpy as np

EXTRACTED_FOLDER = os.path.join(os.path.dirname(__file__), "extracted")
ALIGNED_FOLDER = os.path.join(os.path.dirname(__file__), "aligned")


def _normalize_column_name(name):
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _find_distance_column(columns):
    candidates = [
        "log dist. [ft]",
        "Log Dist. [ft]",
        "log distance",
        "Log Distance",
        "distance",
        "Distance",
        "ILI Wheel Count  [ft.]",
    ]
    normalized_candidates = {_normalize_column_name(c) for c in candidates}
    for col in columns:
        if _normalize_column_name(col) in normalized_candidates:
            return col
    return None


def _load_and_prepare(file_path):
    df = pd.read_csv(file_path)
    distance_col = _find_distance_column(df.columns)
    if distance_col is None:
        raise ValueError(f"No distance column found in {file_path}")

    stem = os.path.splitext(os.path.basename(file_path))[0]
    df = df.copy()
    df["distance_ft"] = pd.to_numeric(df[distance_col], errors="coerce")
    df = df.dropna(subset=["distance_ft"])
    df["distance_ft"] = df["distance_ft"].astype("float64")
    df[f"{stem}__distance_ft"] = df["distance_ft"].astype("float64")

    rename_map = {}
    for col in df.columns:
        if col in {"distance_ft", f"{stem}__distance_ft"}:
            continue
        rename_map[col] = f"{stem}__{col}"
    df = df.rename(columns=rename_map)

    return df, stem


def _extract_year(stem):
    digits = "".join(ch for ch in stem if ch.isdigit())
    for i in range(len(digits) - 3):
        year = int(digits[i : i + 4])
        if 1900 <= year <= 2100:
            return year
    return None


def _pick_delta_order(stems):
    year_map = {stem: _extract_year(stem) for stem in stems}
    if 2007 in year_map.values() and 2015 in year_map.values():
        stem_2007 = next(stem for stem, year in year_map.items() if year == 2007)
        stem_2015 = next(stem for stem, year in year_map.items() if year == 2015)
        return stem_2007, stem_2015
    return stems[0], stems[1]


def _find_column_by_pattern(columns, patterns):
    """Find column matching any of the patterns (case-insensitive)."""
    normalized_patterns = {_normalize_column_name(p) for p in patterns}
    for col in columns:
        if _normalize_column_name(col) in normalized_patterns:
            return col
    return None


def _get_target_columns(stem_a, stem_b, merged_df):
    """Get the target column pairs for avg/delta calculation."""
    target_mappings = {
        "distance_ft": ["log dist. [ft]", "Log Dist. [ft]", "distance", "Distance"],
        "height": ["Height", "height", "Elevation", "elevation"],
        "thickness": ["t [in]", "T [in]", "Wt [in]", "WT [in]", "thickness", "Thickness"],
        "jlength": ["J. len [ft]", "J.len [ft]", "Joint Length", "joint length", "J. length"],
    }
    
    target_cols = {}
    for key, patterns in target_mappings.items():
        col_a = _find_column_by_pattern([col[len(f"{stem_a}__"):] for col in merged_df.columns if col.startswith(f"{stem_a}__")], patterns)
        col_b = _find_column_by_pattern([col[len(f"{stem_b}__"):] for col in merged_df.columns if col.startswith(f"{stem_b}__")], patterns)
        
        if col_a and col_b:
            target_cols[key] = (f"{stem_a}__{col_a}", f"{stem_b}__{col_b}")
    
    return target_cols


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
    os.makedirs(ALIGNED_FOLDER, exist_ok=True)

    csv_files = sorted(glob(os.path.join(EXTRACTED_FOLDER, "*.csv")))
    if not csv_files:
        print(f"No CSV files found in {EXTRACTED_FOLDER}")
        return

    merged_df = None
    stems = []
    for idx, file_path in enumerate(csv_files):
        df, stem = _load_and_prepare(file_path)
        stems.append(stem)
        df = df.sort_values("distance_ft")

        if merged_df is None:
            merged_df = df
            continue

        merged_df = pd.merge_asof(
            merged_df.sort_values("distance_ft"),
            df,
            on="distance_ft",
            direction="nearest",
            tolerance=20.0,
            suffixes=("", f"__{stem}"),
        )

        matched_col = f"{stem}__distance_ft"
        merged_df = merged_df[merged_df[matched_col].notna()]

    if len(stems) >= 2:
        stem_a, stem_b = _pick_delta_order(stems[:2])
        
        # Get target columns for distance, height, thickness, and J.length
        target_cols = _get_target_columns(stem_a, stem_b, merged_df)
        
        # Create new dataframe with id, corrected distance, and other metrics
        result_df = pd.DataFrame()
        result_df["id"] = range(1, len(merged_df) + 1)
        
        # Build drift and compute corrected distance using T(x)=x-Δ(x) from 2007/2015
        dist_a_col = f"{stem_a}__distance_ft"
        dist_b_col = f"{stem_b}__distance_ft"
        dist_a = pd.to_numeric(merged_df[dist_a_col], errors="coerce")
        dist_b = pd.to_numeric(merged_df[dist_b_col], errors="coerce")
        drift_fn = _build_drift_function(dist_a.values, dist_b.values)
        corrected_distance = _apply_coordinate_transform(dist_a.values, drift_fn)
        
        # Store raw distances for later drift correction
        result_df[f"{stem_a}__distance"] = dist_a
        result_df[f"{stem_b}__distance"] = dist_b
        
        result_df.insert(1, "distance_corrected", corrected_distance)
        result_df["distance__delta"] = dist_b - dist_a
        
        # For other metrics, store average and delta
        for key, (col_a, col_b) in target_cols.items():
            if key == "distance_ft":
                continue  # Skip distance as we already handled it separately
            
            series_a = pd.to_numeric(merged_df[col_a], errors="coerce")
            series_b = pd.to_numeric(merged_df[col_b], errors="coerce")
            
            result_df[f"{key}__avg"] = (series_a + series_b) / 2.0
            result_df[f"{key}__delta"] = series_b - series_a
        
        # If r_2022 exists (3+ files), add its columns with suffix _2022
        if len(stems) >= 3:
            stem_2022 = next((s for s in stems if _extract_year(s) == 2022), None)
            if stem_2022:
                # Apply drift correction to r_2022 distances as well
                dist_2022_col = f"{stem_2022}__distance_ft"
                if dist_2022_col in merged_df.columns:
                    dist_2022 = pd.to_numeric(merged_df[dist_2022_col], errors="coerce")
                    result_df["distance_2022"] = dist_2022
                    result_df["distance_2022_corrected"] = _apply_coordinate_transform(dist_2022.values, drift_fn)
                
                # Add other metrics from 2022
                height_2022_col = _find_column_by_pattern(
                    [col[len(f"{stem_2022}__"):] for col in merged_df.columns if col.startswith(f"{stem_2022}__")],
                    ["Height", "height", "Elevation", "elevation"]
                )
                thickness_2022_col = _find_column_by_pattern(
                    [col[len(f"{stem_2022}__"):] for col in merged_df.columns if col.startswith(f"{stem_2022}__")],
                    ["t [in]", "T [in]", "Wt [in]", "WT [in]", "thickness", "Thickness"]
                )
                jlength_2022_col = _find_column_by_pattern(
                    [col[len(f"{stem_2022}__"):] for col in merged_df.columns if col.startswith(f"{stem_2022}__")],
                    ["J. len [ft]", "J.len [ft]", "Joint Length", "joint length", "J. length"]
                )
                
                if height_2022_col:
                    result_df["height_2022"] = pd.to_numeric(merged_df[f"{stem_2022}__{height_2022_col}"], errors="coerce")
                if thickness_2022_col:
                    result_df["thickness_2022"] = pd.to_numeric(merged_df[f"{stem_2022}__{thickness_2022_col}"], errors="coerce")
                if jlength_2022_col:
                    result_df["jlength_2022"] = pd.to_numeric(merged_df[f"{stem_2022}__{jlength_2022_col}"], errors="coerce")
        
        merged_df = result_df

    output_path = os.path.join(ALIGNED_FOLDER, "merged_by_distance.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"Saved merged and averaged data to {output_path}")


if __name__ == "__main__":
    main()