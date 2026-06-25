import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_nav_history():
    print(f"\n{'='*60}")
    print("CLEANING: nav_history.csv")
    print(f"{'='*60}")

    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    print(f"Original shape: {df.shape}")

    # 1. Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    bad_dates = df['date'].isna().sum()
    if bad_dates > 0:
        print(f"⚠️  {bad_dates} rows had unparseable dates — dropping them")
        df = df.dropna(subset=['date'])

    # 2. Sort by amfi_code + date
    df = df.sort_values(['amfi_code', 'date']).reset_index(drop=True)

    # 3. Remove duplicates (same fund + same date)
    dupes = df.duplicated(subset=['amfi_code', 'date']).sum()
    if dupes > 0:
        print(f"⚠️  Removing {dupes} duplicate (amfi_code, date) rows")
        df = df.drop_duplicates(subset=['amfi_code', 'date'], keep='first')

    # 4. Validate NAV > 0
    invalid_nav = (df['nav'] <= 0).sum()
    if invalid_nav > 0:
        print(f"⚠️  {invalid_nav} rows have NAV <= 0 — dropping them")
        df = df[df['nav'] > 0]

    # 5. Forward-fill missing NAV for holidays/weekends
    # Build a complete daily date range PER fund, then forward-fill
    filled_frames = []
    for code, group in df.groupby('amfi_code'):
        group = group.set_index('date').sort_index()
        full_range = pd.date_range(group.index.min(), group.index.max(), freq='D')
        group = group.reindex(full_range)
        group['amfi_code'] = code
        group['nav'] = group['nav'].ffill()
        group['scheme_name'] = group['scheme_name'].ffill() if 'scheme_name' in group.columns else None
        group = group.reset_index().rename(columns={'index': 'date'})
        filled_frames.append(group)

    df_filled = pd.concat(filled_frames, ignore_index=True)
    df_filled = df_filled.dropna(subset=['nav'])  # in case very first day had no value to ffill from

    print(f"Final shape after cleaning + forward-fill: {df_filled.shape}")

    outpath = PROCESSED_DIR / "02_nav_history_cleaned.csv"
    df_filled.to_csv(outpath, index=False)
    print(f"Saved to {outpath}")
    return df_filled


if __name__ == "__main__":
    nav_clean = clean_nav_history()

def clean_investor_transactions():
    print(f"\n{'='*60}")
    print("CLEANING: investor_transactions.csv")
    print(f"{'='*60}")

    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    print(f"Original shape: {df.shape}")

    # 1. Fix date format
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    bad_dates = df['transaction_date'].isna().sum()
    print(f"Unparseable dates: {bad_dates}")
    if bad_dates > 0:
        df = df.dropna(subset=['transaction_date'])

    # 2. Standardize transaction_type (defensive - strip whitespace, fix casing)
    valid_types = {'SIP', 'Lumpsum', 'Redemption'}
    df['transaction_type'] = df['transaction_type'].str.strip()
    unexpected_types = set(df['transaction_type'].unique()) - valid_types
    print(f"Unexpected transaction_type values: {unexpected_types if unexpected_types else 'None'}")

    # 3. Validate amount > 0
    invalid_amount = (df['amount_inr'] <= 0).sum()
    print(f"Rows with amount_inr <= 0: {invalid_amount}")
    if invalid_amount > 0:
        df = df[df['amount_inr'] > 0]

    # 4. Check KYC status enum values
    valid_kyc = {'Verified', 'Pending', 'Rejected'}
    unexpected_kyc = set(df['kyc_status'].unique()) - valid_kyc
    print(f"Unexpected kyc_status values: {unexpected_kyc if unexpected_kyc else 'None'}")

    print(f"Final shape: {df.shape}")

    outpath = PROCESSED_DIR / "08_investor_transactions_cleaned.csv"
    df.to_csv(outpath, index=False)
    print(f"Saved to {outpath}")
    return df


if __name__ == "__main__":
    nav_clean = clean_nav_history()
    transactions_clean = clean_investor_transactions()

def clean_scheme_performance():
    print(f"\n{'='*60}")
    print("CLEANING: scheme_performance.csv")
    print(f"{'='*60}")

    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    print(f"Original shape: {df.shape}")

    # 1. Validate all return values are numeric
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        before_na = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors='coerce')
        after_na = df[col].isna().sum()
        new_failures = after_na - before_na
        if new_failures > 0:
            print(f" {col}: {new_failures} value(s) not numeric — set to NaN")

    non_numeric_rows = df[return_cols].isna().any(axis=1).sum()
    if non_numeric_rows > 0:
        print(f" Dropping {non_numeric_rows} rows with non-numeric returns")
        df = df.dropna(subset=return_cols)

    # 2. Flag anomalies — statistical outliers in returns (|z-score| > 4)
    anomaly_flags = pd.Series(False, index=df.index)
    for col in return_cols:
        z = (df[col] - df[col].mean()) / df[col].std(ddof=0)
        col_outliers = z.abs() > 4
        n_outliers = col_outliers.sum()
        if n_outliers > 0:
            print(f" {col}: {n_outliers} statistical outlier(s) (|z| > 4) — flagged, not dropped")
        anomaly_flags = anomaly_flags | col_outliers

    df['is_anomaly'] = anomaly_flags
    print(f"Total rows flagged as anomalies: {anomaly_flags.sum()}")

    # 3. Check expense_ratio range (0.1% - 2.5%)
    out_of_range = (df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)
    n_out_of_range = out_of_range.sum()
    print(f"Rows with expense_ratio_pct outside 0.1%-2.5%: {n_out_of_range}")
    if n_out_of_range > 0:
        print(f" Dropping {n_out_of_range} rows with out-of-range expense_ratio_pct")
        df = df[~out_of_range]

    print(f"Final shape: {df.shape}")

    outpath = PROCESSED_DIR / "07_scheme_performance_cleaned.csv"
    df.to_csv(outpath, index=False)
    print(f"Saved to {outpath}")
    return df


if __name__ == "__main__":
    nav_clean = clean_nav_history()
    transactions_clean = clean_investor_transactions()
    performance_clean = clean_scheme_performance()