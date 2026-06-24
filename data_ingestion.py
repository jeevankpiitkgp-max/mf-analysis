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
    
    # Step 6: Explore fund master
    print(f"\n\n{'='*60}")
    print("FUND MASTER EXPLORATION")
    print(f"{'='*60}")

    fund_master = dataframes["01_fund_master"]

    print(f"\nUnique fund houses ({fund_master['fund_house'].nunique()}):")
    print(fund_master['fund_house'].unique())

    print(f"\nUnique categories ({fund_master['category'].nunique()}):")
    print(fund_master['category'].unique())

    print(f"\nUnique sub-categories ({fund_master['sub_category'].nunique()}):")
    print(fund_master['sub_category'].unique())

    print(f"\nUnique risk categories ({fund_master['risk_category'].nunique()}):")
    print(fund_master['risk_category'].unique())

    print(f"\nUnique SEBI category codes ({fund_master['sebi_category_code'].nunique()}):")
    print(fund_master['sebi_category_code'].unique())

    print(f"\nAMFI code structure:")
    print(fund_master['amfi_code'].describe())
    print(f"\nSample AMFI codes: {sorted(fund_master['amfi_code'].unique())[:10]}")
    print(f"Min code: {fund_master['amfi_code'].min()}, Max code: {fund_master['amfi_code'].max()}")
    print(f"All codes unique? {fund_master['amfi_code'].is_unique}")