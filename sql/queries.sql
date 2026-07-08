PRAGMA table_info(fact_transactions);
-- 1. Top 5 funds by AUM
SELECT amfi_code, aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT dd.year, dd.month, ROUND(AVG(fn.nav), 2) AS avg_nav
FROM fact_nav fn
JOIN dim_date dd ON fn.date_id = dd.date_id
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;

-- 3. SIP inflow YoY growth
SELECT transaction_type, dd.year,
ROUND(SUM(amount_inr), 2) AS total_inflow
FROM fact_transactions ft
JOIN dim_date dd ON ft.date_id = dd.date_id
WHERE transaction_type = 'SIP'
GROUP BY dd.year
ORDER BY dd.year;

-- 4. Transactions by state
SELECT state, COUNT(*) AS num_transactions,
ROUND(SUM(amount_inr), 2) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense_ratio < 1%
SELECT amfi_code, expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct ASC;

-- 6. Top 5 funds by Sharpe ratio
SELECT amfi_code, sharpe_ratio
FROM fact_performance
ORDER BY sharpe_ratio DESC
LIMIT 5;

-- 7. Funds with negative alpha (underperforming benchmark)
SELECT amfi_code, alpha, return_3yr_pct, benchmark_3yr_pct
FROM fact_performance
WHERE alpha < 0
ORDER BY alpha ASC;

-- 8. Transaction breakdown by KYC status
SELECT kyc_status,
COUNT(*) AS num_transactions,
ROUND(SUM(amount_inr), 2) AS total_amount
FROM fact_transactions
GROUP BY kyc_status
ORDER BY total_amount DESC;

-- 9. Top 5 states by SIP investment
SELECT state, ROUND(SUM(amount_inr), 2) AS total_sip
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY state
ORDER BY total_sip DESC
LIMIT 5;

-- 10. Funds with highest max drawdown risk
SELECT amfi_code, max_drawdown_pct, sharpe_ratio, return_3yr_pct
FROM fact_performance
ORDER BY max_drawdown_pct ASC
LIMIT 5;