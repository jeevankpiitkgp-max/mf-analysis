import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
DB_PATH = Path(__file__).parent / "bluestockmf.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("PRAGMA foreign_keys = OFF"))
    conn.execute(text("DELETE FROM fact_nav"))
    conn.execute(text("DELETE FROM fact_transactions"))
    conn.execute(text("DELETE FROM fact_performance"))
    conn.execute(text("DELETE FROM fact_aum"))
    conn.execute(text("DELETE FROM dim_date"))
    conn.execute(text("DELETE FROM dim_fund"))
    conn.execute(text("PRAGMA foreign_keys = ON"))
    conn.commit()
# ---------- 1. Load cleaned CSVs ----------
nav_df = pd.read_csv(PROCESSED_DIR / "02_nav_history_cleaned.csv", parse_dates=["date"])
txn_df = pd.read_csv(PROCESSED_DIR / "08_investor_transactions_cleaned.csv", parse_dates=["transaction_date"])
perf_df = pd.read_csv(PROCESSED_DIR / "07_scheme_performance_cleaned.csv")

print(f"nav_df: {nav_df.shape}, txn_df: {txn_df.shape}, perf_df: {perf_df.shape}")

# ---------- 2. Build dim_date from all unique dates across files ----------
all_dates = pd.concat([
    nav_df["date"],
    txn_df["transaction_date"],
]).dropna().drop_duplicates().sort_values().reset_index(drop=True)

dim_date = pd.DataFrame({
    "full_date": all_dates.dt.strftime("%Y-%m-%d"),
    "year": all_dates.dt.year,
    "month": all_dates.dt.month,
    "day": all_dates.dt.day,
    "quarter": all_dates.dt.quarter,
    "day_of_week": all_dates.dt.day_name(),
})

dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
print(f"Loaded dim_date: {len(dim_date)} rows")

# Pull back date_id mapping so fact tables can use it
date_lookup = pd.read_sql("SELECT date_id, full_date FROM dim_date", engine)
date_lookup["full_date"] = pd.to_datetime(date_lookup["full_date"])

# ---------- 3. Build dim_fund ----------
fund_cols = ["amfi_code", "scheme_name", "fund_house", "category"]
fund_cols = [c for c in fund_cols if c in perf_df.columns]
dim_fund = perf_df[fund_cols].drop_duplicates(subset=["amfi_code"])

dim_fund.to_sql("dim_fund", engine, if_exists="append", index=False)
print(f"Loaded dim_fund: {len(dim_fund)} rows")

# ---------- 4. Load fact_nav ----------
fact_nav = nav_df.merge(date_lookup, left_on="date", right_on="full_date", how="left")
fact_nav = fact_nav[["amfi_code", "date_id", "nav"]]
fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)
print(f"Loaded fact_nav: {len(fact_nav)} rows (source had {len(nav_df)})")

# ---------- 5. Load fact_transactions ----------
fact_txn = txn_df.merge(date_lookup, left_on="transaction_date", right_on="full_date", how="left")
txn_cols = ["amfi_code", "date_id", "transaction_type", "amount_inr", "kyc_status"]
txn_cols = [c for c in txn_cols if c in fact_txn.columns]
fact_txn = fact_txn[txn_cols]
fact_txn.to_sql("fact_transactions", engine, if_exists="append", index=False)
print(f"Loaded fact_transactions: {len(fact_txn)} rows (source had {len(txn_df)})")

# ---------- 6. Load fact_performance ----------
perf_cols = [c for c in perf_df.columns if c not in ["scheme_name", "fund_house", "category"]]
fact_perf = perf_df[perf_cols]
fact_perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
print(f"Loaded fact_performance: {len(fact_perf)} rows (source had {len(perf_df)})")

# ---------- 7. Verify row counts ----------
print("\n--- ROW COUNT VERIFICATION ---")
for table in ["dim_fund", "dim_date", "fact_nav", "fact_transactions", "fact_performance"]:
    count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table}", engine).iloc[0]["cnt"]
    print(f"{table}: {count} rows")