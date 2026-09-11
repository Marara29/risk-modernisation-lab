DROP TABLE IF EXISTS entity_default_target;

CREATE TABLE entity_default_target AS

SELECT
    m.entity_id,

    CASE
        WHEN MAX(
            CASE
                WHEN d.snapshot_date > '2025-06-30'
                 AND d.snapshot_date <= '2025-12-31'
                 AND d.days_past_due >= 90
                THEN 1
                ELSE 0
            END
        ) = 1
        THEN 1
        ELSE 0
    END AS default_180d

FROM customer_entity_map m

JOIN accounts a
    ON m.customer_record_id = a.customer_record_id

LEFT JOIN delinquencies d
    ON a.account_id = d.account_id

GROUP BY m.entity_id;