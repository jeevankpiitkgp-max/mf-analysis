---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/mf-analysis.git
cd mf-analysis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the ETL pipeline
```bash
python scripts/etl_pipeline.py
```
This will:
- Read all 10 source CSVs from `data/raw/` and `data/processed/`
- Build the 8-table SQLite star schema at `data/db/bluestockmf.db`
- Log all steps and row counts to `logs/etl_pipeline.log`
- Complete in under 5 seconds

### 4. Fetch live NAV data (optional)
```bash
python scripts/live_nav_fetch.py
```
Fetches current NAV for 5 selected schemes from mfapi.in API.

### 5. Open the dashboard
Open `dashboard/bluestock_mf.pbix` in Power BI Desktop.
The dashboard uses pre-exported CSVs from `data/processed/` — no live connection required.

### 6. Run the notebooks
Open any notebook in `notebooks/` using Jupyter or VS Code.
The setup block at the top of each notebook connects to the database using the absolute path pattern:
```python
from pathlib import Path
DB_PATH = Path(r"<your-local-path>\mf-analysis\data\db\bluestockmf.db")
```
Update `DB_PATH` to match your local machine before running.

---

## Database Schema

The SQLite database (`bluestockmf.db`) follows a star schema:

| Table | Type | Rows | Description |
|---|---|---|---|
| `dim_fund` | Dimension | 40 | Fund master — AMC, category, expense ratio |
| `dim_date` | Dimension | 1,608 | Full date dimension with year/month/quarter |
| `fact_nav` | Fact | 64,320 | Daily NAV per scheme |
| `fact_transactions` | Fact | 32,778 | Investor SIP/Lumpsum/Redemption transactions |
| `fact_performance` | Fact | 40 | Sharpe, Sortino, Alpha, Beta, Max Drawdown |
| `fact_aum` | Fact | 90 | Quarterly AUM per fund house |
| `fact_sip_industry` | Fact | 48 | Monthly industry SIP inflow data |
| `fact_portfolio` | Fact | 322 | Equity fund sector holdings |

To recreate the schema from scratch:
```bash
sqlite3 data/db/bluestockmf.db < sql/schema.sql
```

---

## Key Analytical Outputs

| Analysis | Output File |
|---|---|
| Fund Scorecard (composite 0-100) | `reports/fund_scorecard.csv` |
| Alpha & Beta (OLS regression) | `reports/alpha_beta.csv` |
| Sharpe Ratio ranking | `reports/sharpe_values.csv` |
| Sortino Ratio ranking | `reports/sortino_values.csv` |
| Maximum Drawdown | `reports/max_drawdown.csv` |
| CAGR (1yr/3yr/5yr) | `reports/cagr_report.csv` |
| VaR & CVaR (95%) | `reports/var_cvar_report.csv` |
| Sector HHI Concentration | `reports/sector_hhi.csv` |
| Investor Cohort Analysis | `reports/cohort_analysis.csv` |
| SIP Continuity Flags | `reports/sip_continuity.csv` |

---

## Technical Stack

| Category | Tool |
|---|---|
| Language | Python 3.10+ |
| Data Processing | Pandas, NumPy |
| Statistics | SciPy (OLS regression) |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Database | SQLite3 via SQLAlchemy |
| Dashboard | Power BI Desktop |
| Version Control | Git + GitHub |
| Live Data API | mfapi.in (no auth required) |

---

## Known Limitations

- The dataset's NAV history and pre-supplied performance metrics (`fact_performance`) were generated independently — regression-based alpha/beta values are documented as unreliable for this specific dataset. Methodology is validated correct; the limitation lies in data generation.
- Investor transaction data reflects quarterly SIP cadence rather than realistic monthly patterns.
- Dashboard connects via exported CSVs (not live ODBC) due to driver compatibility limitations documented in the project log.

---

## Disclaimer

All data is sourced from publicly available AMFI India, NSE, BSE, and mfapi.in information.
This project is for educational purposes only and does not constitute financial advice.
Mutual Fund investments are subject to market risks.

---

*Bluestock Fintech Pvt. Ltd. | Capstone Project | June 2026*