DROP TABLE IF EXISTS entity_credit_exposure;

CREATE TABLE entity_credit_exposure AS

SELECT
    m.entity_id,

    COUNT(DISTINCT a.account_id) AS account_count,

    SUM(a.credit_limit) AS total_credit_limit,

    SUM(a.current_balance) AS total_current_balance,

    CASE
        WHEN SUM(a.credit_limit) > 0
        THEN SUM(a.current_balance) / SUM(a.credit_limit)
        ELSE NULL
    END AS entity_utilization,

    MAX(a.credit_limit) AS max_single_account_limit,

    MAX(a.current_balance) AS max_single_account_balance,

    SUM(
        CASE
            WHEN a.current_balance IS NULL
            THEN 1
            ELSE 0
        END
    ) AS missing_balance_count

FROM customer_entity_map m

JOIN accounts a
    ON m.customer_record_id = a.customer_record_id

GROUP BY m.entity_id;