import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"

def load_and_inspect(filepath):
    df = pd.read_csv(filepath)
    print(f"\n{'='*60}")
    print(f"FILE: {filepath.name}")
    print(f"{'='*60}")
    print(f"Shape: {df.shape}")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nHead:\n{df.head()}")

    # anomaly checks
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        print(f"\n  Missing values:\n{nulls}")

    dupes = df.duplicated().sum()
    if dupes > 0:
        print(f"\n Duplicate rows: {dupes}")

    # check for columns that look like dates but aren't parsed as dates
    for col in df.columns:
        if df[col].dtype == "object" and any(k in col.lower() for k in ["date", "dt"]):
            print(f"\n Column '{col}' looks like a date but is dtype 'object' — consider parsing with pd.to_datetime()")

    return df

if __name__ == "__main__":
    if not RAW_DIR.exists():
        print(f"ERROR: {RAW_DIR} does not exist.")
        exit()

    csv_files = sorted(RAW_DIR.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files in {RAW_DIR}\n")

    if not csv_files:
        print("No CSV files found. Place your 10 datasets inside data/raw/ and rerun.")
        exit()

    dataframes = {}
    for f in csv_files:
        dataframes[f.stem] = load_and_inspect(f)

    print(f"\n\n{'='*60}")
    print(f"SUMMARY: Loaded {len(dataframes)} datasets")
    print(f"{'='*60}")
    for name, df in dataframes.items():
        print(f"  - {name}: {df.shape[0]} rows × {df.shape[1]} columns")