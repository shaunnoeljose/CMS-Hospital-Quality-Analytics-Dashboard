import pandas as pd
from pathlib import Path

raw_path = Path("data/raw")

files = [
    "hospital_general_information.csv",
    "timely_and_effective_care.csv",
    "complications_and_deaths.csv",
    "patient_experience_hcahps.csv",
    "unplanned_hospital_visits.csv",
]

for file in files:
    path = raw_path / file
    df = pd.read_csv(path, nrows=5)
    print("\n" + "=" * 80)
    print(file)
    print("Rows preview:", df.shape)
    print("Columns:")
    print(df.columns.tolist())
    print(df.head())