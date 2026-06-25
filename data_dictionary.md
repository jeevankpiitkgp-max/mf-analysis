# Data Dictionary — Bluestock MF Capstone

## 1. dim_fund
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | TEXT | Unique AMFI scheme code (Primary Key) |
| scheme_name | TEXT | Full official AMFI scheme name |
| fund_house | TEXT | AMC name (e.g. SBI Mutual Fund) |
| category | TEXT | Equity / Debt / Hybrid |

## 2. dim_date
| Column | Type | Description |
|--------|------|-------------|
| date_id | INTEGER | Auto-generated Primary Key |
| full_date | TEXT | Date in YYYY-MM-DD format |
| year | INTEGER | Year (e.g. 2024) |
| month | INTEGER | Month number (1-12) |
| day | INTEGER | Day of month |
| quarter | INTEGER | Quarter (1-4) |
| day_of_week | TEXT | Day name (e.g. Monday) |

## 3. fact_nav
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | TEXT | Foreign key to dim_fund |
| date_id | INTEGER | Foreign key to dim_date |
| nav | REAL | Net Asset Value in Rs. |

## 4. fact_transactions
| Column | Type | Description |
|--------|------|-------------|
| transaction_id | INTEGER | Primary Key |
| amfi_code | INTEGER | Foreign key to dim_fund |
| date_id | INTEGER | Foreign key to dim_date |
| investor_id | TEXT | Unique investor identifier |
| transaction_type | TEXT | SIP / Lumpsum / Redemption |
| amount_inr | REAL | Transaction amount in Rs. |
| kyc_status | TEXT | Verified / Pending |
| state | TEXT | Investor's Indian state |

## 5. fact_performance
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | TEXT | Foreign key to dim_fund |
| plan | TEXT | Regular or Direct |
| return_1yr_pct | REAL | 1-year return % |
| return_3yr_pct | REAL | 3-year CAGR % |
| return_5yr_pct | REAL | 5-year CAGR % |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR % |
| alpha | REAL | Return above benchmark |
| beta | REAL | Market sensitivity |
| sharpe_ratio | REAL | Risk-adjusted return |
| sortino_ratio | REAL | Downside risk-adjusted return |
| std_dev_ann_pct | REAL | Annualised standard deviation % |
| max_drawdown_pct | REAL | Worst peak-to-trough decline |
| aum_crore | REAL | Assets under management in Rs. crore |
| expense_ratio_pct | REAL | Annual expense ratio % |
| morningstar_rating | INTEGER | 1-5 star rating |
| risk_grade | TEXT | Low / Moderate / High / Very High |
| is_anomaly | INTEGER | 1 if anomaly detected, 0 otherwise |

## Data Sources
| Dataset | Source |
|---------|--------|
| NAV History | mfapi.in / AMFI India |
| Investor Transactions | Simulated (real distributions) |
| Scheme Performance | Computed from NAV history |
| Fund Master | AMFI India public data |