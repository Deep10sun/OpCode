import pandas as pd
import os

# Get the processed folder path
processed_folder = os.path.join(os.path.dirname(__file__), "processed")
aligned_folder = os.path.join(os.path.dirname(__file__), "extracted")
os.makedirs(aligned_folder, exist_ok=True)

# Define files and their corresponding column names
files_to_process = [
    {
        "file": "r_2007_processed.csv",
        "event_col": "event",
        "log_dist_col": "log dist. [ft]",
        "clock_col": "o'clock"
    },
    {
        "file": "r_2015_processed.csv",
        "event_col": "Event Description",
        "log_dist_col": "Log Dist. [ft]",
        "clock_col": "O'clock"
    },
    {
        "file": "r_2022_processed.csv",
        "event_col": "Event Description",
        "log_dist_col": "ILI Wheel Count \n[ft.]",
        "clock_col": "O'clock\n[hh:mm]"
    },
]

for file_info in files_to_process:
    filename = file_info["file"]
    event_col = file_info["event_col"]
    log_dist_col = file_info["log_dist_col"]
    clock_col = file_info["clock_col"]
    
    file_path = os.path.join(processed_folder, filename)
    df = pd.read_csv(file_path)
    
    # Extract rows where event column contains "Weld"
    try:
        weld_rows = df[df[event_col].astype(str).str.contains('Weld', case=False, na=False)].copy()
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        continue
    
    # Delete columns that have all NaN values
    weld_rows = weld_rows.dropna(axis=1, how='all')
    # Add 1-based sequential id column at the start
    weld_rows.insert(0, "id", range(1, len(weld_rows) + 1))

    print(f"Total rows in {filename}: {len(df)}")
    print(f"Weld rows: {len(weld_rows)}")
    print(f"Columns: {list(weld_rows.columns)}")
    print(f"First few weld rows:")
    print(weld_rows.head())
    
    # Save weld rows to extracted folder
    output_filename = filename.replace("_processed.csv", "_weld_aligned.csv")
    output_path = os.path.join(aligned_folder, output_filename)
    weld_rows.to_csv(output_path, index=False)
    print(f"Saved weld rows to {output_filename}\n")