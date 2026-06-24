# Day 1 — Data Quality Summary

## Dataset Ingestion
All 10 provided CSV datasets loaded successfully with no read errors.
Total records ingested: ~91,000+ rows across all files combined.

## Key Findings

### 1. Date columns need type conversion
Several files store date columns as string/object type rather than 
datetime: nav_history, aum_by_fund_house, monthly_sip_inflows, 
category_inflows, industry_folio_count, investor_transactions, 
portfolio_holdings, benchmark_indices. To be converted with 
pd.to_datetime() in the processing stage.

### 2. Missing values
monthly_sip_inflows has 12 missing values in yoy_growth_pct — expected,
since YoY growth requires a full prior year of trailing data.

### 3. No duplicate rows
No duplicate records detected across any of the 10 files.

### 4. AMFI code validation (fund_master ↔ nav_history) — PASSED
- fund_master: 40 unique AMFI codes
- nav_history: 40 unique AMFI codes
- Match rate: 100% — every code in fund_master has corresponding NAV 
  history, and vice versa
- Each scheme has exactly 1,150 NAV records (fully consistent time 
  series across all schemes, no gaps in coverage)

### 5. Fund master structure
- 10 fund houses, 2 broad categories (Equity/Debt), 12 sub-categories,
  5 risk grades, 9 SEBI category codes
- AMFI codes are unique integer identifiers (range: 100016–149324) 
  with no embedded structural meaning — i.e., not a fixed-width 
  encoding scheme, just sequential/arbitrary IDs issued by AMFI

### 6. Live API data (mfapi.in) — code/name mismatch
The 6 AMFI codes provided in the task brief for live NAV fetching do 
not correctly map to their labeled scheme names (e.g., code 125497 
labeled "HDFC Top 100 Direct" actually returns SBI Mutual Fund data).
Only Nippon Large Cap (118632) was correctly labeled. The underlying 
NAV data was still fetched successfully for all 6 codes — only the 
name-to-code mapping in the brief is unreliable. Recommend verifying 
current AMFI codes via amfiindia.com before using for fund-specific 
reporting.

## Overall Assessment
The internal datasets (10 CSVs) are clean, consistent, and fully 
cross-validated — suitable for downstream analysis with minor dtype 
conversions. The external API data is usable but requires code 
verification before attributing to specific fund names.