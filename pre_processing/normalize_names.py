import os
import pandas as pd

folder_path = os.path.join(os.path.dirname(__file__), "processed")

dfs = []   # list to store each run's dataframe
i = 1
for filename in os.listdir(folder_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path)
        df["run_id"] = i
        dfs.append(df)
    i += 1
rename_map_r2007 = {
    "t": "thickness [in]",
    "to u/s w. [ft]": "upstream [ft]",
    "to d/s w. [ft]": "downstream [ft]",
    "log dist. [ft]": "distance [ft]",
    "event": "type",
    "depth [%]": "depth [%]",
    "length [in]": "length [in]",
    "width [in]": "width [in]",
    "internal" : "I/E",
    "o'clock": "clock",
}

rename_map_r2015 = {
    "Wt [in]": "thickness [in]",
    "to u/s w. [ft]": "upstream [ft]",
    "to d/s w. [ft]": "downstream [ft]",
    "Log Dist. [ft]": "distance [ft]",
    "Event Description": "type",
    "Depth [%]": "depth [%]",
    "Length [in]": "length [in]",
    "Width [in]": "width [in]",
    "ID/OD" : "I/E",
    "O'clock": "clock",
}
rename_map_r2025 = {
    "WT [in]": "thickness [in]",
    "Distance to U/S GW [ft]": "upstream [ft]",
    "Distance to D/S GW [ft]": "downstream [ft]",
    "ILI Wheel Count [ft.]": "distance [ft]",
    "Event Description": "type",
    "Metal Loss Depth [%]": "depth [%]",
    "Length [in]": "length [in]",
    "Width [in]": "width [in]",
    "ID/OD" : "I/E",
    "O'clock [hh:mm]": "clock",
}

# rename
dfs[0] = dfs[0].rename(columns=rename_map_r2007)
dfs[1] = dfs[1].rename(columns=rename_map_r2015)
dfs[2] = dfs[2].rename(columns=rename_map_r2025)

dfs[0]["downstream [ft]"] = 0

# save to processed folder
output_folder = os.path.join(os.path.dirname(__file__), "processed")
output_path = os.path.join(output_folder, "r_2007_processed.csv")
dfs[0].to_csv(output_path, index=False)

output_path = os.path.join(output_folder, "r_2015_processed.csv")
dfs[1].to_csv(output_path, index=False)

output_path = os.path.join(output_folder, "r_2022_processed.csv")
dfs[2].to_csv(output_path, index=False)