import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

DB_PATH = r"D:\code\mf-analysis\bluestockmf.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

fund_master = pd.read_sql("SELECT * FROM dim_fund", engine)
dim_date = pd.read_sql("SELECT * FROM dim_date", engine, parse_dates=["full_date"])
nav = pd.read_sql("SELECT * FROM fact_nav", engine)
txn_raw = pd.read_csv("data/raw/08_investor_transactions.csv", parse_dates=["transaction_date"])
holdings = pd.read_sql("SELECT * FROM fact_portfolio", engine)
performance = pd.read_sql("SELECT * FROM fact_performance", engine)

nav = nav.merge(dim_date[["date_id","full_date"]], on="date_id", how="left")
nav = nav.merge(fund_master[["amfi_code","scheme_name","category"]], on="amfi_code", how="left")

# Compute daily returns on trading days only (lesson learned from Day 4)
nav = nav[nav["full_date"].dt.dayofweek < 5].copy()
nav = nav.sort_values(["amfi_code","full_date"])
nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

print("Setup complete:", nav.shape)

performance = pd.read_sql("SELECT * FROM fact_performance", engine)
fund_master = pd.read_sql("SELECT * FROM dim_fund", engine)
perf_enriched = performance.merge(fund_master[["amfi_code","scheme_name"]], on="amfi_code")

def recommend_funds(risk_appetite):
    risk_map = {
        "Low": ["Low"],
        "Moderate": ["Moderate"],
        "High": ["High", "Very High"]
    }
    
    if risk_appetite not in risk_map:
        print("Invalid input. Choose: Low, Moderate, or High")
        return
    
    valid_grades = risk_map[risk_appetite]
    filtered = perf_enriched[perf_enriched["risk_grade"].isin(valid_grades)]
    top3 = filtered.nlargest(3, "sharpe_ratio")[["scheme_name","sharpe_ratio","risk_grade","return_3yr_pct"]]
    
    print(f"\nTop 3 Fund Recommendations for {risk_appetite} Risk Appetite:")
    print(top3.to_string(index=False))
    return top3

recommend_funds("Low")
recommend_funds("Moderate")
recommend_funds("High")