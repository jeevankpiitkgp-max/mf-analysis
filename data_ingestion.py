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
    #  Validate AMFI codes between fund_master and nav_history
    print(f"\n\n{'='*60}")
    print("STEP 7: AMFI CODE VALIDATION")
    print(f"{'='*60}")

    nav_history = dataframes["02_nav_history"]

    master_codes = set(fund_master['amfi_code'].unique())
    nav_codes = set(nav_history['amfi_code'].unique())

    missing_in_nav = master_codes - nav_codes
    extra_in_nav = nav_codes - master_codes
    matched = master_codes & nav_codes

    print(f"\nTotal codes in fund_master: {len(master_codes)}")
    print(f"Total unique codes in nav_history: {len(nav_codes)}")
    print(f"Matched codes (in both): {len(matched)}")
    print(f"Codes in fund_master but MISSING from nav_history: {len(missing_in_nav)}")
    if missing_in_nav:
        print(f"  → {sorted(missing_in_nav)}")
    print(f"Codes in nav_history but NOT in fund_master: {len(extra_in_nav)}")
    if extra_in_nav:
        print(f"  → {sorted(extra_in_nav)}")

    match_pct = (len(matched) / len(master_codes)) * 100
    print(f"\nMatch rate: {match_pct:.1f}% of fund_master codes have NAV history")

    # records per scheme - sanity check
    records_per_code = nav_history.groupby('amfi_code').size()
    print(f"\nNAV records per scheme — min: {records_per_code.min()}, max: {records_per_code.max()}, avg: {records_per_code.mean():.0f}")