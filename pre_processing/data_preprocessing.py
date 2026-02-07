import pandas as pd
import os
from glob import glob

# Get the data folder path
data_folder = os.path.join(os.path.dirname(__file__), "..", "data")

# Load all r_*.csv files
csv_files = glob(os.path.join(data_folder, "r_*.csv"))

# Create a dictionary to store dataframes
dataframes = {}

for file_path in sorted(csv_files):
    filename = os.path.basename(file_path)
    key = filename.replace(".csv", "")
    df = pd.read_csv(file_path)
    original_shape = df.shape

    # Find columns that are completely NaN/Null
    null_columns = df.columns[df.isnull().all()].tolist()
    # Delete columns with all NaN/Null values
    df = df.drop(columns=null_columns)

    # Delete rows where all values are NaN/Null
    df = df.dropna(how='all')

    dataframes[key] = df

    print(f"Loaded {filename}")
    print(f"  Original shape: {original_shape}")
    if null_columns:
        print(f"  Deleted {len(null_columns)} completely empty columns: {null_columns}")
    print(f"  Final shape: {df.shape}")

print(f"\nProcessed {len(dataframes)} dataframes")

# Save processed dataframes to processed folder
output_folder = os.path.join(os.path.dirname(__file__), "processed")
os.makedirs(output_folder, exist_ok=True)
print("\nSaving processed dataframes...")

for name, df in dataframes.items():
    output_path = os.path.join(output_folder, f"{name}_processed.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved {name}_processed.csv")
