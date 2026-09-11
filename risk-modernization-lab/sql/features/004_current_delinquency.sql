DROP TABLE IF EXISTS entity_current_delinquency;

CREATE TABLE entity_current_delinquency AS

SELECT
    m.entity_id,

    MAX(d.days_past_due) AS current_max_dpd,

    CASE
        WHEN MAX(d.days_past_due) >= 90
        THEN 1
        ELSE 0
    END AS currently_defaulted

FROM customer_entity_map m

JOIN accounts a
    ON m.customer_record_id = a.customer_record_id

LEFT JOIN delinquencies d
    ON a.account_id = d.account_id
   AND d.snapshot_date = '2025-06-30'

GROUP BY m.entity_id;

--What we’re checking is simple:
---currently_defaulted = 0
--→ eligible for PD prediction

--currently_defaulted = 1
--→ already in default at scoring date
--→ usually exclude from PD development population