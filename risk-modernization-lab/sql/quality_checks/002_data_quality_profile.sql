-- ==========================================================
-- RISK MODERNIZATION LAB
-- Data Quality Profile
-- ==========================================================


-- ----------------------------------------------------------
-- 1. Customer records with no accounts
-- ----------------------------------------------------------

SELECT
    COUNT(*) AS customer_records_without_accounts
FROM customer_records c
LEFT JOIN accounts a
    ON c.customer_record_id = a.customer_record_id
WHERE a.account_id IS NULL;


-- ----------------------------------------------------------
-- 2. Check whether those records have applications
-- ----------------------------------------------------------

SELECT
    COUNT(DISTINCT c.customer_record_id) AS no_account_but_has_application
FROM customer_records c

LEFT JOIN accounts a
    ON c.customer_record_id = a.customer_record_id

INNER JOIN applications app
    ON c.customer_record_id = app.customer_record_id

WHERE a.account_id IS NULL;


-- ----------------------------------------------------------
-- 3. Missing identity fields
-- ----------------------------------------------------------

SELECT
    COUNT(*) AS total_records,

    SUM(CASE WHEN phone IS NULL THEN 1 ELSE 0 END)
        AS missing_phone,

    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END)
        AS missing_email,

    SUM(CASE WHEN address IS NULL THEN 1 ELSE 0 END)
        AS missing_address

FROM customer_records;


-- ----------------------------------------------------------
-- 4. Completely weak identity records
-- ----------------------------------------------------------

SELECT *
FROM customer_records
WHERE phone IS NULL
  AND email IS NULL
  AND address IS NULL;


-- ----------------------------------------------------------
-- 5. Duplicate phone numbers
-- ----------------------------------------------------------

SELECT
    phone,
    COUNT(*) AS customer_records

FROM customer_records

WHERE phone IS NOT NULL

GROUP BY phone

HAVING COUNT(*) > 1

ORDER BY customer_records DESC;


-- ----------------------------------------------------------
-- 6. Duplicate email addresses
-- ----------------------------------------------------------

SELECT
    email,
    COUNT(*) AS customer_records

FROM customer_records

WHERE email IS NOT NULL

GROUP BY email

HAVING COUNT(*) > 1

ORDER BY customer_records DESC;


-- ----------------------------------------------------------
-- 7. Duplicate addresses
-- ----------------------------------------------------------

SELECT
    address,
    city,
    state,
    COUNT(*) AS customer_records

FROM customer_records

WHERE address IS NOT NULL

GROUP BY
    address,
    city,
    state

HAVING COUNT(*) > 1

ORDER BY customer_records DESC;


-- ----------------------------------------------------------
-- 8. Account-level missingness
-- ----------------------------------------------------------

SELECT
    COUNT(*) AS total_accounts,

    SUM(
        CASE WHEN current_balance IS NULL
        THEN 1 ELSE 0 END
    ) AS missing_balance,

    SUM(
        CASE WHEN credit_limit IS NULL
        THEN 1 ELSE 0 END
    ) AS missing_limit

FROM accounts;


-- ----------------------------------------------------------
-- 9. Invalid / unusual account conditions
-- ----------------------------------------------------------

SELECT
    SUM(CASE WHEN credit_limit <= 0 THEN 1 ELSE 0 END)
        AS nonpositive_limits,

    SUM(CASE WHEN current_balance < 0 THEN 1 ELSE 0 END)
        AS negative_balances,

    SUM(
        CASE
            WHEN current_balance > credit_limit
            THEN 1 ELSE 0
        END
    ) AS over_limit_accounts

FROM accounts;


-- ----------------------------------------------------------
-- 10. Credit-limit distribution
-- ----------------------------------------------------------

SELECT

    COUNT(*) AS accounts,

    ROUND(AVG(credit_limit), 2)
        AS avg_credit_limit,

    MIN(credit_limit)
        AS min_credit_limit,

    MAX(credit_limit)
        AS max_credit_limit

FROM accounts;


-- ----------------------------------------------------------
-- 11. Missing transaction fields
-- ----------------------------------------------------------

SELECT

    COUNT(*) AS total_transactions,

    SUM(
        CASE WHEN merchant_category IS NULL
        THEN 1 ELSE 0 END
    ) AS missing_merchant_category,

    SUM(
        CASE WHEN merchant_id IS NULL
        THEN 1 ELSE 0 END
    ) AS missing_merchant_id,

    SUM(
        CASE WHEN country IS NULL
        THEN 1 ELSE 0 END
    ) AS missing_country

FROM transactions;


-- ----------------------------------------------------------
-- 12. Transaction sign profile
-- ----------------------------------------------------------

SELECT

    CASE
        WHEN amount < 0 THEN 'NEGATIVE'
        WHEN amount = 0 THEN 'ZERO'
        ELSE 'POSITIVE'
    END AS transaction_type,

    COUNT(*) AS transaction_count,

    ROUND(AVG(ABS(amount)), 2)
        AS avg_absolute_amount

FROM transactions

GROUP BY transaction_type;


-- ----------------------------------------------------------
-- 13. Duplicate primary business records
-- ----------------------------------------------------------

SELECT
    account_id,
    COUNT(*) AS occurrences

FROM accounts

GROUP BY account_id

HAVING COUNT(*) > 1;


-- ----------------------------------------------------------
-- 14. Orphan accounts
-- accounts pointing to nonexistent customer records
-- ----------------------------------------------------------

SELECT
    COUNT(*) AS orphan_accounts

FROM accounts a

LEFT JOIN customer_records c
    ON a.customer_record_id = c.customer_record_id

WHERE c.customer_record_id IS NULL;


-- ----------------------------------------------------------
-- 15. Orphan transactions
-- transactions pointing to nonexistent accounts
-- ----------------------------------------------------------

SELECT
    COUNT(*) AS orphan_transactions

FROM transactions t

LEFT JOIN accounts a
    ON t.account_id = a.account_id

WHERE a.account_id IS NULL;