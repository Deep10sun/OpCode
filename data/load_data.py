import pandas as pd
import os

path = "/Users/deep10sun/Downloads/ILIDataV2.xlsx"

summary = pd.read_excel(path, sheet_name="Summary")
r_2007 = pd.read_excel(path, sheet_name="2007")
r_2015 = pd.read_excel(path, sheet_name="2015")
r_2022 = pd.read_excel(path, sheet_name="2022")

# Save dataframes to data folder
data_folder = os.path.dirname(__file__)

summary.to_csv(os.path.join(data_folder, "summary.csv"), index=False)
r_2007.to_csv(os.path.join(data_folder, "r_2007.csv"), index=False)
r_2015.to_csv(os.path.join(data_folder, "r_2015.csv"), index=False)
r_2022.to_csv(os.path.join(data_folder, "r_2022.csv"), index=False)