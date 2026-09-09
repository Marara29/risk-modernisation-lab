-- Starter exploration / quality checks

-- There are more customer records than real entities by design. We created 3,500 underlying entities but you see 4,446 source customer_records. That means some real-world businesses are represented more than once)
-- 1) Row counts (-- The database is populated correctly. You have 4,446 customer records, 9,060 accounts, 241,122 transactions, 179,885 payments, 184,588 delinquency snapshots, and 9,060 vendor scores.)
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

-- 2) Missing account values  (current_balance has missing values. You found 144 missing balances out of 9,060 accounts, about 1.6%. We should not immediately fill them with zero. Zero means “known balance is zero”; NULL means “balance is unknown/missing.” Those are different business meanings.)
SELECT
    SUM(CASE WHEN credit_limit IS NULL THEN 1 ELSE 0 END) AS missing_credit_limit,
    SUM(CASE WHEN current_balance IS NULL THEN 1 ELSE 0 END) AS missing_current_balance
FROM accounts;

-- 3) Suspicious/extreme limits (The extreme credit limits are a real data-quality flag. A008305 has a limit around $838K, while most of the high end is near $125K. That should trigger investigation. It might be a real large account, a unit problem, a duplication, or an injected outlier. We should flag it first, not delete it.)
SELECT account_id, credit_limit, current_balance
FROM accounts
ORDER BY credit_limit DESC
LIMIT 20;

-- 4) Negative transactions (could be reversals/refunds; investigate before calling them errors and The 1,985 negative transactions are not automatically errors. They could represent refunds, reversals, credits, corrections, or chargebacks. This is exactly the kind of mistake analysts make if they “clean” data too aggressively. First we classify the business meaning.)
SELECT COUNT(*) AS negative_transaction_count
FROM transactions
WHERE amount < 0;

-- 5) Accounts per customer record (Some customer records have up to 5 accounts. That is important, but this is still only record-level aggregation. Later entity resolution may reveal that multiple customer_record_ids belong to the same real customer, so one entity could have even more total accounts than this query shows.)
SELECT customer_record_id, COUNT(*) AS account_count
FROM accounts
GROUP BY customer_record_id
ORDER BY account_count DESC
LIMIT 20;
