DROP TABLE IF EXISTS pd_modeling_mart;

CREATE TABLE pd_modeling_mart AS

SELECT
    e.entity_id,

    -- -------------------------
    -- Exposure features
    -- -------------------------
    e.account_count,
    e.total_credit_limit,
    e.total_current_balance,
    e.entity_utilization,
    e.max_single_account_limit,
    e.max_single_account_balance,
    e.missing_balance_count,

    -- -------------------------
    -- Historical delinquency
    -- -------------------------
    d.max_dpd_history,
    d.accounts_ever_30_dpd,
    d.accounts_ever_60_dpd,
    d.accounts_ever_90_dpd,
    d.delinquent_snapshots_30plus,
    d.ever_30_dpd,
    d.ever_60_dpd,
    d.ever_90_dpd,

    -- -------------------------
    -- Current status
    -- -------------------------
    c.current_max_dpd,
    c.currently_defaulted,

    -- -------------------------
    -- Target
    -- -------------------------
    t.default_180d

FROM entity_credit_exposure e

JOIN entity_delinquency_features d
    ON e.entity_id = d.entity_id

JOIN entity_current_delinquency c
    ON e.entity_id = c.entity_id

JOIN entity_default_target t
    ON e.entity_id = t.entity_id

WHERE c.currently_defaulted = 0;


--Before June 30, we had 3,525 entities with accounts in the population.

--Then we checked their status on 2025-06-30:

--3,525 total entities with accounts

--294 already defaulted
--3,231 not currently defaulted

--So for the PD model, we kept the 3,231 non-defaulted entities.

--Then, looking forward into the 180-day prediction window, 345 of those 3,231 later defaulted.

--Utilization: min   4.3%avg  42.1%  max  86.4%

--That looks plausible—no utilization over 100%, no negatives, nothing obviously broken.

--Historical severe delinquency is very predictive:

--Never had 90+ DPD before:3,026 entities,235 defaults later,7.77% future default rate

--Had 90+ DPD before, but recovered by scoring date: 205 entities,110 defaults later,53.66% future default rate

--And current delinquency is even clearer:

--Current DPD   Future default rate
--0             3.36%
--30           41.85%
--60           74.64%

--That’s exactly the kind of monotonic relationship we’d hope to see:

--worse current delinquency
        ↓
--higher future default probability