DROP TABLE IF EXISTS entity_delinquency_features;

CREATE TABLE entity_delinquency_features AS

SELECT
    m.entity_id,

    MAX(d.days_past_due)
        AS max_dpd_history,

    COUNT(
        DISTINCT CASE
            WHEN d.days_past_due >= 30
            THEN d.account_id
        END
    ) AS accounts_ever_30_dpd,

    COUNT(
        DISTINCT CASE
            WHEN d.days_past_due >= 60
            THEN d.account_id
        END
    ) AS accounts_ever_60_dpd,

    COUNT(
        DISTINCT CASE
            WHEN d.days_past_due >= 90
            THEN d.account_id
        END
    ) AS accounts_ever_90_dpd,

    SUM(
        CASE
            WHEN d.days_past_due >= 30
            THEN 1
            ELSE 0
        END
    ) AS delinquent_snapshots_30plus,

    CASE
        WHEN MAX(d.days_past_due) >= 30
        THEN 1
        ELSE 0
    END AS ever_30_dpd,

    CASE
        WHEN MAX(d.days_past_due) >= 60
        THEN 1
        ELSE 0
    END AS ever_60_dpd,

    CASE
        WHEN MAX(d.days_past_due) >= 90
        THEN 1
        ELSE 0
    END AS ever_90_dpd

FROM customer_entity_map m

JOIN accounts a
    ON m.customer_record_id = a.customer_record_id

LEFT JOIN delinquencies d
    ON a.account_id = d.account_id

    -- CRITICAL:
    -- only information available at scoring time
    AND d.snapshot_date <= '2025-06-30'

GROUP BY m.entity_id;