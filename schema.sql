CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code TEXT PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date TEXT UNIQUE,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER,
    day_of_week TEXT
);

CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code TEXT,
    date_id INTEGER,
    nav REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date_id INTEGER,
    investor_id TEXT,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL,
    kyc_status TEXT,
    state TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    is_anomaly INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house TEXT,
    date_id INTEGER,
    aum_crore REAL,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);