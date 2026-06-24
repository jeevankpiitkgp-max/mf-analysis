Anomalies identified
1. Date columns across multiple files (nav_history, aum_by_fund_house, 
   monthly_sip_inflows, category_inflows, industry_folio_count, 
   investor_transactions, portfolio_holdings, benchmark_indices) are 
   stored as string/object type rather than datetime. Will convert 
   using pd.to_datetime() during processing stage.
2. monthly_sip_inflows has 12 missing values in yoy_growth_pct — 
   expected, since YoY growth requires a full prior year of data 
   (first 12 months of the series).
3. No duplicate rows detected in any of the 10 files.
4. fund_master and scheme_performance both contain 40 records — 
   to be cross-validated for matching AMFI codes in Step 7.