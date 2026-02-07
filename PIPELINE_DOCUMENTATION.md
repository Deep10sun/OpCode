# Complete Pipeline Documentation

## Overview

The pipeline processes raw inspection data through multiple stages to produce a final drift-corrected dataset with aligned measurements from 2007, 2015, and 2022 inspections.

## Pipeline Stages

### Stage 1: Load Raw Data
**Script**: `data/load_data.py`
- Reads from `/Users/deep10sun/Downloads/ILIDataV2.xlsx`
- Extracts sheets: Summary, 2007, 2015, 2022
- Outputs to `/data/r_*.csv`

### Stage 2: Data Preprocessing
**Script**: `pre_processing/data_preprocessing.py`
- Removes columns with all NaN/Null values
- Removes rows with all NaN/Null values
- Outputs to `/pre_processing/processed/r_*_processed.csv`

### Stage 3: Extract Weld Events
**Script**: `pre_processing/extract.py`
- Filters for weld events (rows containing "Weld")
- Extracts relevant columns (distance, thickness, joint length, clock)
- Adds sequential id column
- Outputs to `/pre_processing/extracted/r_*_weld_aligned.csv`

### Stage 4: Merge & Align with Drift Correction
**Script**: `pre_processing/align.py`
- Merges three datasets using `pd.merge_asof()` on distance (5 ft tolerance)
- Builds piecewise-linear drift function Δ(x) from 2007/2015 pairs
- Applies coordinate transform T(x) = x - Δ(x)
- Preserves raw distances for later use
- Outputs to `/pre_processing/aligned/merged_by_distance.csv`

### Stage 5: Apply Final Drift Correction
**Script**: `pre_processing/apply_drift_correction.py`
- Rebuilds drift function from preserved raw distances
- Applies drift correction to:
  - `distance_corrected` (replaces with doubly-corrected version)
  - `distance_2022` (creates `distance_2022_corrected`)
- Adds `run_id` column (set to 0)
- **Outputs to `/pre_processing/aligned/merged_by_distance_corrected.csv`** ⭐ FINAL OUTPUT

## Running the Pipeline

### Option 1: Complete End-to-End (Recommended)
```bash
cd /Users/deep10sun/Coding/OpCode
python main.py
```
This runs:
1. `data/load_data.py` - Load raw data
2. `full_pipeline.py` - Complete preprocessing & alignment pipeline

### Option 2: Just the Processing Pipeline
```bash
cd /Users/deep10sun/Coding/OpCode/pre_processing
python run_pipeline.py
```
(Assumes data is already in `/data/`)

### Option 3: Individual Steps
```bash
cd /Users/deep10sun/Coding/OpCode/pre_processing

# Preprocess raw data
python data_preprocessing.py

# Extract welds
python extract.py

# Merge and align
python align.py

# Apply final drift correction
python apply_drift_correction.py
```

## Final Output Format

**File**: `pre_processing/aligned/merged_by_distance_corrected.csv`

### Columns:
- **id** - Unique identifier for each weld (1-indexed)
- **distance_corrected** - 2007 distance after double drift correction (ft)
- **distance__delta** - 2015 raw distance - 2007 raw distance (ft)
- **distance_2022** - 2022 raw distance (ft)
- **distance_2022_corrected** - 2022 distance after drift correction (ft)
- **thickness__avg** - Average thickness between 2007 and 2015 (inches)
- **thickness__delta** - 2015 thickness - 2007 thickness (inches)
- **thickness_2022** - 2022 thickness (inches)
- **jlength__avg** - Average joint length between 2007 and 2015 (ft)
- **jlength__delta** - 2015 joint length - 2007 joint length (ft)
- **jlength_2022** - 2022 joint length (ft)
- **r_2007_weld_aligned__distance** - 2007 raw distance (for reference)
- **r_2015_weld_aligned__distance** - 2015 raw distance (for reference)
- **run_id** - Run identifier (currently 0)

### Data Characteristics:
- **Rows**: 1,602 aligned weld locations
- **Alignment method**: Piecewise-linear drift function
- **Distance tolerance**: ±5 ft for merging
- **Coordinate system**: All distances aligned to corrected baseline

## Key Concepts

### Drift Function Δ(x)
The difference between 2015 and 2007 measurements at each weld:
```
Δ(x) = x_2015 - x_2007
```

### Coordinate Transform T(x)
Corrects any distance measurement using:
```
T(x) = x - Δ(x)
```

### Double Correction
Applied because the first corrected distance is used as input for the second drift correction:
1. `x_2007_corrected = x_2007 - Δ(x_2007)`
2. `x_2007_doubly_corrected = x_2007_corrected - Δ(x_2007_corrected)`

## File Structure

```
OpCode/
├── main.py                          # Entry point - calls full pipeline
├── full_pipeline.py                 # Orchestrates all stages
├── data/
│   ├── load_data.py                 # Load from Excel
│   ├── r_2007.csv                   # Raw data
│   ├── r_2015.csv
│   ├── r_2022.csv
│   └── summary.csv
└── pre_processing/
    ├── run_pipeline.py              # Preprocessing pipeline orchestrator
    ├── data_preprocessing.py         # Stage 2: Clean data
    ├── extract.py                   # Stage 3: Extract welds
    ├── align.py                     # Stage 4: Merge & align
    ├── apply_drift_correction.py     # Stage 5: Final correction
    ├── processed/
    │   ├── r_2007_processed.csv
    │   ├── r_2015_processed.csv
    │   └── r_2022_processed.csv
    ├── extracted/
    │   ├── r_2007_weld_aligned.csv
    │   ├── r_2015_weld_aligned.csv
    │   └── r_2022_weld_aligned.csv
    └── aligned/
        ├── merged_by_distance.csv
        └── merged_by_distance_corrected.csv  ⭐ FINAL OUTPUT
```

## Usage Example

```python
import pandas as pd

# Load the final corrected data
df = pd.read_csv("pre_processing/aligned/merged_by_distance_corrected.csv")

# Filter by distance range
nearby_welds = df[(df['distance_corrected'] >= 100) & (df['distance_corrected'] <= 200)]

# Analyze changes between inspections
thickness_change = df['thickness__delta']
distance_drift = df['distance_2022_vs_corrected']

# Compare 2022 vs baseline
print(df[['id', 'distance_corrected', 'thickness__avg', 'thickness_2022']].head())
```

## Notes

- All distances are in feet
- Thickness values are in inches
- The drift function is built only from weld pairs present in all three datasets
- Missing values are handled with NaN coercion and dropna operations
- The pipeline is idempotent - running it multiple times produces the same result
