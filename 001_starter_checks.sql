-- Starter exploration / quality checks

-- 1) Row counts
SELECT 'customer_records' AS table_name, COUNT(*) AS row_count FROM customer_records
UNION ALL
SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL
SELECT 'applications', COUNT(*) FROM applications
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'delinquencies', COUNT(*) FROM delinquencies
UNION ALL
SELECT 'vendor_scores', COUNT(*) FROM vendor_scores;

-- 2) Missing account values
SELECT
    SUM(CASE WHEN credit_limit IS NULL THEN 1 ELSE 0 END) AS missing_credit_limit,
    SUM(CASE WHEN current_balance IS NULL THEN 1 ELSE 0 END) AS missing_current_balance
FROM accounts;

-- 3) Suspicious/extreme limits
SELECT account_id, credit_limit, current_balance
FROM accounts
ORDER BY credit_limit DESC
LIMIT 20;

-- 4) Negative transactions (could be reversals/refunds; investigate before calling them errors)
SELECT COUNT(*) AS negative_transaction_count
FROM transactions
WHERE amount < 0;

-- 5) Accounts per customer record
SELECT customer_record_id, COUNT(*) AS account_count
FROM accounts
GROUP BY customer_record_id
ORDER BY account_count DESC
LIMIT 20;
