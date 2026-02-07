import pandas as pd
import os
from glob import glob

# Get the data folder path
data_folder = os.path.join(os.path.dirname(__file__), "data")

# Load all r_*.csv files
csv_files = glob(os.path.join(data_folder, "r_*.csv"))

# Create a dictionary to store dataframes
dataframes = {}

for file_path in sorted(csv_files):
    filename = os.path.basename(file_path)
    # Remove .csv extension to use as key
    key = filename.replace(".csv", "")
    dataframes[key] = pd.read_csv(file_path)
    print(f"Loaded {filename}")