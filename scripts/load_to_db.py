"""
===============================================================
Bluestock Fintech — Mutual Fund Analytics Platform
ETL Pipeline (Master Run Script)
---------------------------------------------------------------
Usage:  python scripts/etl_pipeline.py
Output: bluestockmf.db (SQLite) + logs/etl_pipeline.log
===============================================================
"""

import sys
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text, inspect

# ─────────────────────────────────────────────
# PATHS — all relative to project root
# ─────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent   # project root
DATA_RAW      = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DB_PATH       = BASE_DIR / "data" / "db" / "bluestockmf.db"
LOG_DIR       = BASE_DIR / "logs"

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "etl_pipeline.log"),
        logging.StreamHandler(sys.stdout),        # also print to terminal
    ],
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def read_csv(filepath: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV with error handling. Raises on failure."""
    if not filepath.exists():
        log.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Missing: {filepath}")
    try:
        df = pd.read_csv(filepath, **kwargs)
        log.info(f"  Read {filepath.name}: {df.shape[0]:,} rows, {df.shape[1]} cols")
        return df
    except Exception as e:
        log.error(f"  Failed to read {filepath.name}: {e}")
        raise


def clear_table(engine, table_name: str) -> None:
    """Delete all rows from a table, keeping the schema intact."""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
        log.info(f"  Cleared table: {table_name}")
    except Exception as e:
        log.warning(f"  Could not clear {table_name} (may not exist yet): {e}")


def load_table(df: pd.DataFrame, table_name: str, engine) -> None:
    """Append a DataFrame to a table with error handling."""
    if df is None or df.empty:
        log.warning(f"  Skipping {table_name} — DataFrame is empty")
        return
    try:
        df.to_sql(table_name, engine, if_exists="append", index=False)
        count = pd.read_sql(
            f"SELECT COUNT(*) as cnt FROM {table_name}", engine
        ).iloc[0]["cnt"]
        log.info(f"   {table_name}: {count:,} rows now in table")
    except Exception as e:
        log.error(f"  Failed to load {table_name}: {e}")
        raise


def verify_counts(engine) -> None:
    """Print and log final row counts for all 8 tables."""
    log.info("\n--- ROW COUNT VERIFICATION ---")
    tables = [
        "dim_fund", "dim_date", "fact_nav", "fact_transactions",
        "fact_performance", "fact_aum", "fact_sip_industry", "fact_portfolio"
    ]
    for table in tables:
        try:
            count = pd.read_sql(
                f"SELECT COUNT(*) as cnt FROM {table}", engine
            ).iloc[0]["cnt"]
            log.info(f"  {table:<25}: {count:>7,} rows")
        except Exception as e:
            log.warning(f"  {table:<25}: could not query — {e}")


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Bluestock Fintech — ETL Pipeline Started")
    log.info("=" * 60)

    # ── 0. Database connection ──────────────────
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        log.info(f"Connected to database: {DB_PATH}")
    except Exception as e:
        log.critical(f"Cannot connect to database: {e}")
        sys.exit(1)

    # ── 1. Load cleaned source CSVs ────────────
    log.info("\n[1] Loading source CSVs...")
    try:
        nav_df  = read_csv(DATA_PROCESSED / "02_nav_history_cleaned.csv",
                           parse_dates=["date"])
        txn_df  = read_csv(DATA_PROCESSED / "08_investor_transactions_cleaned.csv",
                           parse_dates=["transaction_date"])
        perf_df = read_csv(DATA_PROCESSED / "07_scheme_performance_cleaned.csv")
        sip_df  = read_csv(DATA_RAW / "04_monthly_sip_inflows.csv")
        holdings_df = read_csv(DATA_RAW / "09_portfolio_holdings.csv")
        aum_df  = read_csv(DATA_RAW / "03_aum_by_fund_house.csv",
                           parse_dates=["date"])
    except FileNotFoundError:
        log.critical("One or more source files are missing. Aborting.")
        sys.exit(1)

    # ── 2. Clear existing fact/dim tables ──────
    log.info("\n[2] Clearing existing tables...")
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            for tbl in ["fact_nav", "fact_transactions", "fact_performance",
                        "fact_aum", "fact_sip_industry", "fact_portfolio",
                        "dim_date", "dim_fund"]:
                conn.execute(text(f"DELETE FROM {tbl}"))
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()
        log.info("  All tables cleared")
    except Exception as e:
        log.error(f"  Error clearing tables: {e}")
        sys.exit(1)

    # ── 3. Build dim_date ──────────────────────
    log.info("\n[3] Building dim_date...")
    try:
        all_dates = pd.concat([
            nav_df["date"],
            txn_df["transaction_date"],
        ]).dropna().drop_duplicates().sort_values().reset_index(drop=True)

        dim_date = pd.DataFrame({
            "full_date"   : all_dates.dt.strftime("%Y-%m-%d"),
            "year"        : all_dates.dt.year,
            "month"       : all_dates.dt.month,
            "day"         : all_dates.dt.day,
            "quarter"     : all_dates.dt.quarter,
            "day_of_week" : all_dates.dt.day_name(),
        })
        load_table(dim_date, "dim_date", engine)
    except Exception as e:
        log.error(f"  dim_date build failed: {e}")
        sys.exit(1)

    # ── 4. Pull date_id lookup ─────────────────
    try:
        date_lookup = pd.read_sql("SELECT date_id, full_date FROM dim_date", engine)
        date_lookup["full_date"] = pd.to_datetime(date_lookup["full_date"])
        log.info(f"  date_lookup loaded: {len(date_lookup):,} entries")
    except Exception as e:
        log.error(f"  Failed to load date_lookup: {e}")
        sys.exit(1)

    # ── 5. Build dim_fund ──────────────────────
    log.info("\n[4] Building dim_fund...")
    try:
        fund_cols = [c for c in ["amfi_code","scheme_name","fund_house","category"]
                     if c in perf_df.columns]
        dim_fund = perf_df[fund_cols].drop_duplicates(subset=["amfi_code"])
        load_table(dim_fund, "dim_fund", engine)
    except Exception as e:
        log.error(f"  dim_fund build failed: {e}")
        sys.exit(1)

    # ── 6. Load fact_nav ───────────────────────
    log.info("\n[5] Loading fact_nav...")
    try:
        fact_nav = nav_df.merge(
            date_lookup, left_on="date", right_on="full_date", how="left"
        )
        null_dates = fact_nav["date_id"].isna().sum()
        if null_dates > 0:
            log.warning(f"  {null_dates:,} NAV rows had no matching date_id — will be dropped")
        fact_nav = fact_nav[["amfi_code","date_id","nav"]].dropna(subset=["date_id"])
        load_table(fact_nav, "fact_nav", engine)
    except Exception as e:
        log.error(f"  fact_nav load failed: {e}")
        sys.exit(1)

    # ── 7. Load fact_transactions ──────────────
    log.info("\n[6] Loading fact_transactions...")
    try:
        fact_txn = txn_df.merge(
            date_lookup, left_on="transaction_date", right_on="full_date", how="left"
        )
        txn_cols = [c for c in
                    ["amfi_code","date_id","investor_id","transaction_type",
                     "amount_inr","kyc_status","state"]
                    if c in fact_txn.columns]
        fact_txn = fact_txn[txn_cols].dropna(subset=["date_id"])
        load_table(fact_txn, "fact_transactions", engine)
    except Exception as e:
        log.error(f"  fact_transactions load failed: {e}")
        sys.exit(1)

    # ── 8. Load fact_performance ───────────────
    log.info("\n[7] Loading fact_performance...")
    try:
        perf_cols = [c for c in perf_df.columns
                     if c not in ["scheme_name","fund_house","category"]]
        fact_perf = perf_df[perf_cols]
        load_table(fact_perf, "fact_performance", engine)
    except Exception as e:
        log.error(f"  fact_performance load failed: {e}")
        sys.exit(1)

    # ── 9. Load fact_aum ───────────────────────
    log.info("\n[8] Loading fact_aum...")
    try:
        aum_df["date"] = pd.to_datetime(aum_df["date"])
        aum_merged = pd.merge_asof(
            aum_df.sort_values("date"),
            date_lookup.sort_values("full_date"),
            left_on="date", right_on="full_date",
            direction="nearest"
        )
        null_dates = aum_merged["date_id"].isna().sum()
        if null_dates > 0:
            log.warning(f"  {null_dates} AUM rows had no matching date_id")
        fact_aum = aum_merged[["fund_house","date_id","aum_crore"]].dropna(subset=["date_id"])
        load_table(fact_aum, "fact_aum", engine)
    except Exception as e:
        log.error(f"  fact_aum load failed: {e}")
        sys.exit(1)

    # ── 10. Load fact_sip_industry ─────────────
    log.info("\n[9] Loading fact_sip_industry...")
    try:
        sip_df["month"] = pd.to_datetime(sip_df["month"])
        date_lookup["month_start"] = date_lookup["full_date"].values.astype("datetime64[M]")
        sip_df["match_date"] = sip_df["month"].values.astype("datetime64[M]")

        sip_merged = sip_df.merge(
            date_lookup.drop_duplicates("month_start")[["date_id","month_start"]],
            left_on="match_date", right_on="month_start", how="left"
        )
        null_dates = sip_merged["date_id"].isna().sum()
        if null_dates > 0:
            log.warning(f"  {null_dates} SIP rows had no matching date_id")

        sip_cols = [c for c in
                    ["date_id","sip_inflow_crore","active_sip_accounts_crore",
                     "new_sip_accounts_lakh","sip_aum_lakh_crore","yoy_growth_pct"]
                    if c in sip_merged.columns]
        fact_sip = sip_merged[sip_cols].dropna(subset=["date_id"])
        load_table(fact_sip, "fact_sip_industry", engine)
    except Exception as e:
        log.error(f"  fact_sip_industry load failed: {e}")
        sys.exit(1)

    # ── 11. Load fact_portfolio ────────────────
    log.info("\n[10] Loading fact_portfolio...")
    try:
        holdings_df["portfolio_date"] = pd.to_datetime(holdings_df["portfolio_date"])
        holdings_merged = holdings_df.merge(
            date_lookup[["date_id","full_date"]],
            left_on="portfolio_date", right_on="full_date", how="left"
        )
        null_dates = holdings_merged["date_id"].isna().sum()
        if null_dates > 0:
            log.warning(f"  {null_dates} portfolio rows had no matching date_id")

        fact_portfolio = holdings_merged[
            ["amfi_code","stock_symbol","weight_pct","sector","date_id"]
        ].dropna(subset=["date_id"])
        load_table(fact_portfolio, "fact_portfolio", engine)
    except Exception as e:
        log.error(f"  fact_portfolio load failed: {e}")
        sys.exit(1)

    # ── 12. Final verification ─────────────────
    log.info("\n[11] Verifying row counts...")
    verify_counts(engine)

    # ── 13. Duplicate check for portfolio ──────
    try:
        dupes = pd.read_sql(
            """SELECT amfi_code, stock_symbol, sector, date_id, COUNT(*) c
               FROM fact_portfolio
               GROUP BY amfi_code, stock_symbol, sector, date_id
               HAVING c > 1""",
            engine
        )
        if dupes.empty:
            log.info("  No duplicate rows found in fact_portfolio ")
        else:
            log.warning(f"  {len(dupes)} duplicate rows found in fact_portfolio ")
    except Exception as e:
        log.warning(f"  Duplicate check failed: {e}")

    log.info("\n" + "=" * 60)
    log.info("ETL Pipeline Completed Successfully")
    log.info("=" * 60)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.critical(f"Unhandled error: {e}")
        sys.exit(1)