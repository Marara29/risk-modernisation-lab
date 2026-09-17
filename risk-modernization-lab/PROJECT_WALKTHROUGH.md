# Risk Modernization Lab — End-to-End Project Walkthrough

This document explains the entire project from raw data ingestion through entity resolution, PD modeling, calibration, risk bands, monitoring, and vendor benchmarking.

It is written so that someone opening the repository for the first time can understand:

- what each file does,
- why each step exists,
- what order to run things in,
- what business problem each step solves,
- what outputs were produced,
- what decisions were made,
- and what limitations still remain.

---

# 1. Project Goal

The goal of this project is to simulate a realistic credit-risk modernization workflow.

Instead of starting with a clean modeling table, the project starts with raw operational-style data:

- customer records,
- accounts,
- applications,
- transactions,
- payments,
- delinquency snapshots,
- vendor risk scores.

The core business problem is:

> Build a trustworthy internal probability-of-default workflow from messy account-level data, resolve customer identities, create point-in-time risk features, train and validate an internal PD model, convert model output into useful risk bands and decisions, monitor the model, and compare it against an existing vendor score.

The project intentionally emphasizes the full workflow rather than only model training.

---

# 2. High-Level Architecture

```text
Raw data
   |
   v
Data quality checks
   |
   v
Customer identity normalization
   |
   v
Candidate pair generation
   |
   v
Entity resolution
   |
   v
Customer entity map
   |
   v
Entity-level credit + delinquency features
   |
   v
Point-in-time PD modeling mart
   |
   v
Logistic regression baseline
   |
   v
Threshold analysis
   |
   v
Feature simplification
   |
   v
Calibration
   |
   v
Risk bands
   |
   v
Monitoring
   |
   v
Vendor vs internal benchmark
```

---

# 3. Repository Structure

Recommended structure:

```text
risk-modernization-lab/
|
├── data/
│   └── reference/
│       └── entity_truth_DO_NOT_USE_FOR_MODELING.csv
|
├── database/
│   └── risk_lab.db
|
├── sql/
│   ├── schemas/
│   │   └── 001_raw_tables.sql
│   |
│   └── features/
│       ├── 001_entity_exposure.sql
│       ├── 002_entity_delinquency.sql
│       ├── 003_default_target.sql
│       ├── 004_current_delinquency.sql
│       └── 005_pd_modeling_mart.sql
|
├── src/
│   ├── load_raw_data.py
│   |
│   ├── entity_resolution/
│   │   ├── 01_normalize_customers.py
│   │   ├── 02_generate_candidates.py
│   │   ├── 03_score_candidates.py
│   │   ├── 04_classify_matches.py
│   │   ├── 05_evaluate_matches.py
│   │   ├── 06_inspect_false_negatives.py
│   │   └── 07_build_entities.py
│   |
│   ├── models/
│   │   ├── 01_logistic_pd_baseline.py
│   │   ├── 02_threshold_analysis.py
│   │   ├── 03_feature_correlation.py
│   │   ├── 04_logistic_pd_v2.py
│   │   └── 05_vendor_vs_internal.py
│   |
│   └── monitoring/
│       ├── 01_pd_monitoring.py
│       └── 02_model_performance.py
|
└── PROJECT_WALKTHROUGH.md
```

---

# 4. Environment and Database

The project uses SQLite for the lab database.

Database file:

```text
database/risk_lab.db
```

Open it with:

```bash
sqlite3 database/risk_lab.db
```

Important lesson:

```bash
sqlite3
```

by itself opens a temporary in-memory SQLite session.

Always provide the database file path when you want to inspect the project database.

---

# 5. Raw Schema Creation

File:

```text
sql/schemas/001_raw_tables.sql
```

## Purpose

This file creates the raw database tables.

The schema defines the structure of the data, but it does not load any rows.

Typical raw tables in the project:

```text
customer_records
accounts
applications
transactions
payments
delinquencies
vendor_scores
```

## Why this step matters

Separating schema creation from data loading makes the workflow reproducible.

The schema answers:

> What fields exist and how are the raw systems represented?

The loader answers:

> How do we populate those tables?

---

# 6. Raw Data Loading

File:

```text
src/load_raw_data.py
```

## Purpose

Loads the raw synthetic source data into:

```text
database/risk_lab.db
```

## Important lesson

Creating SQL tables does not load the data.

The Python loader must run after the schema exists.

## Row counts after loading

```text
customer_records  = 4,446
accounts           = 9,060
applications       = 9,060
transactions       = 241,122
payments           = 179,885
delinquencies      = 184,588
vendor_scores      = 9,060
```

---

# 7. Initial Data Quality Review

Before modeling, the project checks whether the source data is usable.

## Customer identity

Missing values found:

```text
name     = 0
phone    = 117
email    = 111
address  = 101
```

No customer had phone, email, and address all missing at the same time.

This means identity resolution is possible, but individual identity fields are incomplete.

## Accounts

```text
missing credit_limit    = 0
missing current_balance = 144
```

Credit-limit range:

```text
min = 2,500
avg ≈ 14,791
max ≈ 838,493 on one account
```

The large maximum was treated as an outlier to investigate, not automatically delete.

## Transactions

```text
241,122 total transactions
1,985 negative transactions
≈ 0.82%
```

Negative transactions may represent refunds or reversals, so they were kept rather than automatically removed.

Missing merchant category:

```text
2,306
```

## Referential integrity

Checks showed:

```text
no duplicate account IDs
no orphan accounts
no orphan transactions
```

## Modeling-readiness conclusion

```text
Customer identity      = yellow
Account integrity      = green
Balances / limits      = yellow
Transactions           = yellow
Referential integrity  = green
Modeling readiness     = red until identity is resolved
```

The main blocker was not SQL integrity.

It was customer identity.

---

# 8. Entity Resolution

The same real customer may appear more than once in source systems.

Example:

```text
John Smith
john smith
JOHN SMITH
```

or:

```text
6309 Lake Road
6309 LAKE RD
```

If these records are not linked, total exposure and delinquency can be split across multiple fake customers.

If records are incorrectly merged, two different customers can be combined.

This is why entity resolution is foundational.

---

# 9. Customer Normalization

File:

```text
src/entity_resolution/01_normalize_customers.py
```

## Purpose

Creates a standardized identity representation.

Typical normalization includes:

- lowercase names,
- whitespace cleanup,
- phone digits only,
- lowercase emails,
- standardized address abbreviations,
- normalized city/state text.

Output table:

```text
customer_identity_normalized
```

## Why this matters

Raw strings that look different can become identical after normalization.

Example:

```text
6309 LAKE RD
6309 Lake Rd
```

can both normalize to:

```text
6309 lake rd
```

This improves downstream matching.

---

# 10. Candidate Pair Generation

File:

```text
src/entity_resolution/02_generate_candidates.py
```

## Purpose

Avoid comparing every customer record with every other customer record.

Instead, generate only plausible record pairs using blocking rules.

Primary candidate-generation signals included exact normalized matches on:

```text
phone
email
address + city + state
```

Experiments later considered additional blockers such as:

```text
name
email domain
```

but looser matching was not used for automatic merges.

## Why this matters

Entity resolution has two separate problems:

```text
1. Did two records ever get compared?
2. If compared, did the match logic classify them correctly?
```

A true duplicate that never becomes a candidate cannot be recovered by better scoring.

---

# 11. Candidate Scoring

File:

```text
src/entity_resolution/03_score_candidates.py
```

## Purpose

Create matching evidence for every candidate pair.

Features:

```text
phone_match
email_match
address_match
name_match
```

Original simple score:

```text
4 * phone_match
+ 3 * email_match
+ 2 * address_match
+ 1 * name_match
```

## Why this matters

This creates an interpretable matching signal before the final merge decision.

---

# 12. Match Classification

File:

```text
src/entity_resolution/04_classify_matches.py
```

## Purpose

Classify candidate pairs into:

```text
MATCH
REVIEW
NO_MATCH
```

The policy intentionally prioritizes precision.

Examples of automatic MATCH evidence:

```text
phone + email + address
phone + email + name
phone + address + name
phone + email
phone + address
email + address + name
```

Examples sent to REVIEW:

```text
phone + name
email + address
address + name
email + name
```

## Result

```text
MATCH      = 935
REVIEW     = 2,219
NO_MATCH   = 1,676
```

## Why high precision was chosen

A false merge can incorrectly combine:

- exposure,
- delinquency,
- balances,
- credit limits,
- account history.

In credit risk, false merges can contaminate downstream risk estimates.

Therefore, ambiguous cases were left for possible analyst / risk-operations / data-quality review rather than automatically merged.

---

# 13. Entity Resolution Evaluation

File:

```text
src/entity_resolution/05_evaluate_matches.py
```

## Purpose

Evaluate entity-resolution quality against hidden synthetic truth.

Truth file:

```text
data/reference/entity_truth_DO_NOT_USE_FOR_MODELING.csv
```

Important:

This truth file is only for evaluation.

It must never be used as a modeling feature.

## V1 evaluation

```text
True duplicate pairs = 982
Predicted MATCH      = 935

TP = 935
FP = 0
FN = 47

Precision = 1.000
Recall    = 0.952
F1        = 0.975
```

## Interpretation

Precision:

```text
Of the pairs we merged,
how many were truly the same entity?
```

Result:

```text
100%
```

Recall:

```text
Of all true duplicate pairs,
how many did we successfully merge?
```

Result:

```text
95.2%
```

The project accepted some false splits in exchange for avoiding false merges.

---

# 14. Rejected Looser Matching Experiment

An experiment added looser signals such as:

```text
exact normalized name
email domain
```

and more permissive match rules.

Result:

```text
TP = 937
FP = 324
FN = 45

Precision = 0.743
Recall    = 0.954
F1        = 0.835
```

Recall barely improved, but false merges increased dramatically.

This version was rejected.

## Lesson

Higher recall is not automatically better.

In identity resolution:

```text
small recall gain
can be unacceptable
if false merges explode
```

---

# 15. False-Negative Diagnostics

File:

```text
src/entity_resolution/06_inspect_false_negatives.py
```

## Purpose

Understand why true duplicate records were missed.

Observed patterns included:

- same phone + name but email prefix changed,
- same email + address but name variation,
- missing phone,
- minor name spelling variations,
- some pairs never generated as candidates.

## Important lesson

A false negative can come from:

```text
candidate-generation failure
```

or:

```text
classification/scoring failure
```

Those are different problems and should be diagnosed separately.

The project intentionally stopped optimizing entity resolution once the high-precision V1 policy was considered acceptable.

---

# 16. Build Resolved Entities

File:

```text
src/entity_resolution/07_build_entities.py
```

## Purpose

Convert MATCH pairs into customer clusters.

Method:

```text
Union-Find / Disjoint Set
```

Output table:

```text
customer_entity_map
```

This table maps:

```text
customer_record_id -> entity_id
```

## Result

```text
Source customer records = 4,446
Resolved entities       = 3,545
Largest entity groups   = 3 records
```

Synthetic truth contained approximately:

```text
3,500 true entities
```

The extra resolved entities are consistent with the conservative false-split strategy.

---

# 17. Entity-Level Credit Exposure

File:

```text
sql/features/001_entity_exposure.sql
```

Output:

```text
entity_credit_exposure
```

## Purpose

Aggregate account-level exposure to the resolved customer entity.

Fields include:

```text
entity_id
account_count
total_credit_limit
total_current_balance
entity_utilization
max_single_account_limit
max_single_account_balance
missing_balance_count
```

## Key result

```text
entities_with_accounts = 3,525
avg_accounts           = 2.57
max_accounts           = 5
avg_total_limit        ≈ 38,016
avg_total_balance      ≈ 15,502
avg_utilization        ≈ 42.2%
```

## Important nuance

SQLite `SUM()` ignores NULL values.

Therefore:

```text
total_current_balance
```

can still be incomplete when individual account balances are missing.

That is why:

```text
missing_balance_count
```

is retained.

---

# 18. Modeling Timeline

Scoring / as-of date:

```text
2025-06-30
```

Observation window:

```text
all information available on or before 2025-06-30
```

Future performance window:

```text
2025-07-01 through 2025-12-31
```

The modeling rule is:

```text
X must be known before prediction
y must happen after prediction
```

This prevents target leakage.

---

# 19. Historical Delinquency Features

File:

```text
sql/features/002_entity_delinquency.sql
```

Output:

```text
entity_delinquency_features
```

## Purpose

Build delinquency-history features using only information available by the scoring date.

Filter:

```sql
snapshot_date <= '2025-06-30'
```

Features include:

```text
max_dpd_history
accounts_ever_30_dpd
accounts_ever_60_dpd
accounts_ever_90_dpd
delinquent_snapshots_30plus
ever_30_dpd
ever_60_dpd
ever_90_dpd
```

## Result

```text
entities ever 30+ DPD = 1,352
entities ever 60+ DPD = 705
entities ever 90+ DPD = 499
avg max DPD            ≈ 21.8
```

Max-DPD distribution:

```text
0 DPD   = 2,173
30 DPD  = 647
60 DPD  = 206
90 DPD  = 499
```

---

# 20. Future Default Target

File:

```text
sql/features/003_default_target.sql
```

Output:

```text
entity_default_target
```

## Target definition

```text
default_180d = 1
```

if any linked account reaches:

```text
days_past_due >= 90
```

during:

```text
2025-07-01 through 2025-12-31
```

## Initial result before eligibility filtering

```text
entities         = 3,525
future defaults  = 627
default rate     = 17.79%
```

This rate was inflated because some customers were already defaulted at the scoring date.

---

# 21. Current Delinquency Status

File:

```text
sql/features/004_current_delinquency.sql
```

Output:

```text
entity_current_delinquency
```

## Purpose

Determine eligibility at the scoring date.

Fields:

```text
current_max_dpd
currently_defaulted
```

Current status at:

```text
2025-06-30
```

## Result

```text
current_max_dpd = 0   -> 2,795 entities
current_max_dpd = 30  -> 227 entities
current_max_dpd = 60  -> 209 entities
current_max_dpd = 90  -> 294 entities
```

Already defaulted:

```text
294
```

These entities were excluded from PD modeling.

## Why

The model is intended to predict future default among customers who have not already defaulted.

---

# 22. PD Modeling Mart

File:

```text
sql/features/005_pd_modeling_mart.sql
```

Output:

```text
pd_modeling_mart
```

## Purpose

Join:

```text
entity_credit_exposure
entity_delinquency_features
entity_current_delinquency
entity_default_target
```

and keep only eligible customers:

```sql
WHERE currently_defaulted = 0
```

## Final mart

```text
rows             = 3,231
future defaults  = 345
non-defaults     = 2,886
default rate     = 10.68%
```

This is the actual model-training population.

---

# 23. Sanity Checks Before Modeling

## Utilization

```text
min ≈ 4.27%
avg ≈ 42.09%
max ≈ 86.44%
```

## Historical severe delinquency

```text
ever_90_dpd = 0
entities = 3,026
future defaults = 235
future default rate = 7.77%

ever_90_dpd = 1
entities = 205
future defaults = 110
future default rate = 53.66%
```

## Current delinquency

```text
current DPD = 0
future default rate = 3.36%

current DPD = 30
future default rate = 41.85%

current DPD = 60
future default rate = 74.64%
```

The direction is sensible:

```text
higher delinquency
-> higher future default risk
```

---

# 24. Baseline Logistic Regression

File:

```text
src/models/01_logistic_pd_baseline.py
```

## Purpose

Train a simple, interpretable PD baseline.

Why logistic regression:

- strong baseline,
- fast,
- interpretable,
- common in risk modeling,
- useful before trying more complex models.

## Initial feature set

```text
account_count
total_credit_limit
total_current_balance
entity_utilization
max_single_account_limit
max_single_account_balance
missing_balance_count
max_dpd_history
accounts_ever_30_dpd
accounts_ever_60_dpd
accounts_ever_90_dpd
delinquent_snapshots_30plus
ever_30_dpd
ever_60_dpd
ever_90_dpd
current_max_dpd
```

## Pipeline

```text
median imputation
-> standardization
-> logistic regression
```

## Split

```text
Train      = 1,938
Validation = 646
Test       = 647
```

The split is stratified to preserve the default rate.

Important limitation:

This is a random stratified split because the current synthetic mart is a single scoring-date cohort.

A more production-realistic setup would create multiple scoring cohorts and use out-of-time validation.

---

# 25. Baseline Model Performance

Validation:

```text
ROC-AUC = 0.822
PR-AUC  = 0.570
```

Confusion matrix at threshold 0.50:

```text
TN = 566
FP = 11
FN = 34
TP = 35
```

Positive-class performance:

```text
Precision = 76.1%
Recall    = 50.7%
F1        = 60.9%
```

## Interpretation

Recall asks:

```text
Of all actual defaults,
how many did the model catch?
```

Precision asks:

```text
Of all customers flagged as default-risk,
how many actually defaulted?
```

False-positive rate asks:

```text
Of all actual non-defaulters,
how many were incorrectly flagged?
```

---

# 26. Threshold Analysis

File:

```text
src/models/02_threshold_analysis.py
```

## Purpose

The default 0.50 threshold is arbitrary.

A customer with:

```text
PD = 0.30
```

may still be extremely risky in a portfolio whose default rate is only 10.68%.

Thresholds tested:

```text
0.50
0.40
0.30
0.20
0.10
```

Validation results:

| Threshold | Precision | Recall | F1 | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.761 | 0.507 | 0.609 | 35 | 11 | 34 | 566 |
| 0.40 | 0.672 | 0.565 | 0.614 | 39 | 19 | 30 | 558 |
| 0.30 | 0.570 | 0.652 | 0.608 | 45 | 34 | 24 | 543 |
| 0.20 | 0.566 | 0.681 | 0.618 | 47 | 36 | 22 | 541 |
| 0.10 | 0.500 | 0.696 | 0.582 | 48 | 48 | 21 | 529 |

## Decision

Threshold:

```text
0.20
```

was chosen as a reasonable validation tradeoff.

Why not 0.10?

Going from:

```text
0.20 -> 0.10
```

caught only one extra default but produced many more false positives.

---

# 27. Untouched Test Evaluation

The 0.20 threshold was selected using validation data and then locked.

Final test result:

```text
Precision = 0.568
Recall    = 0.667
F1        = 0.613

TP = 46
FP = 35
FN = 23
TN = 543
```

False-positive rate:

```text
35 / 578 ≈ 6.1%
```

Plain-English interpretation:

> At the selected threshold, the model catches about two-thirds of future defaults while incorrectly flagging about 6% of non-defaulters.

---

# 28. Logistic Coefficient Review

The initial coefficient review showed:

```text
current_max_dpd                +1.068
delinquent_snapshots_30plus    +0.582
ever_90_dpd                    -0.480
total_credit_limit             +0.477
ever_60_dpd                    -0.469
...
```

Some coefficient signs were counterintuitive.

The reason was suspected multicollinearity.

A coefficient should not be read as a simple standalone correlation.

It means:

> the effect of this feature while other model features are held constant.

When several features encode nearly the same delinquency behavior, signs can become unstable.

---

# 29. Feature Correlation Review

File:

```text
src/models/03_feature_correlation.py
```

## Purpose

Identify highly redundant features.

Examples:

```text
accounts_ever_90_dpd <-> ever_90_dpd = 0.967
accounts_ever_60_dpd <-> ever_60_dpd = 0.953
accounts_ever_30_dpd <-> ever_30_dpd = 0.913

total_current_balance <-> max_single_account_balance = 0.902
total_credit_limit <-> total_current_balance = 0.890
total_credit_limit <-> max_single_account_limit = 0.863
```

The delinquency features contained substantial duplicate information.

---

# 30. Simplified PD Model V2

File:

```text
src/models/04_logistic_pd_v2.py
```

## Purpose

Reduce feature redundancy while preserving predictive performance.

Final V2 feature set:

```text
account_count
total_credit_limit
entity_utilization
missing_balance_count
current_max_dpd
delinquent_snapshots_30plus
ever_90_dpd
```

## Why these features

```text
account_count
-> number of linked accounts

total_credit_limit
-> entity-level total exposure

entity_utilization
-> share of available credit currently used

missing_balance_count
-> data-quality / missingness signal

current_max_dpd
-> current delinquency severity

delinquent_snapshots_30plus
-> repeated delinquency behavior

ever_90_dpd
-> history of severe delinquency
```

---

# 31. Model V2 Validation

```text
ROC-AUC = 0.844
PR-AUC  = 0.575
```

Threshold results:

| Threshold | Precision | Recall | F1 | TP | FP | FN | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.745 | 0.507 | 0.603 | 35 | 12 | 34 | 565 |
| 0.40 | 0.731 | 0.551 | 0.628 | 38 | 14 | 31 | 563 |
| 0.30 | 0.656 | 0.609 | 0.632 | 42 | 22 | 27 | 555 |
| 0.20 | 0.566 | 0.681 | 0.618 | 47 | 36 | 22 | 541 |
| 0.10 | 0.516 | 0.696 | 0.593 | 48 | 45 | 21 | 532 |

## Decision

Model V2 became the working PD model.

Reasons:

```text
16 features -> 7 features
less redundancy
easier to explain
slightly better validation ROC-AUC
similar threshold behavior
```

---

# 32. V2 Coefficients

```text
current_max_dpd                +1.0878
delinquent_snapshots_30plus    +0.6627
ever_90_dpd                    -0.3954
entity_utilization             +0.1704
total_credit_limit             +0.0915
account_count                  +0.0323
missing_balance_count          -0.0087
```

The strongest signals remained:

```text
current delinquency
repeated delinquency
```

The negative coefficient on `ever_90_dpd` was not interpreted as “past 90-DPD is protective.”

It was treated cautiously because the feature still overlaps with the other delinquency variables.

---

# 33. Calibration

Calibration was checked inside:

```text
src/models/04_logistic_pd_v2.py
```

## Purpose

ROC-AUC answers:

```text
Can the model rank risky customers above safe customers?
```

Calibration answers:

```text
When the model says PD = 20%,
does roughly 20% of that group actually default?
```

## Result

Brier score:

```text
0.0583
```

Calibration buckets:

```text
predicted 2.59% -> actual 0.77%
predicted 3.09% -> actual 5.43%
predicted 3.53% -> actual 4.65%
predicted 4.32% -> actual 4.65%
predicted 39.60% -> actual 37.98%
```

The model was especially well aligned in the high-risk bucket.

The low-risk buckets showed some mismatch, so individual PDs should not be treated as perfectly exact.

---

# 34. Risk Bands

Also built inside:

```text
src/models/04_logistic_pd_v2.py
```

Risk bands:

```text
LOW
MEDIUM
HIGH
VERY_HIGH
```

Example cutoffs:

```text
LOW       < 5%
MEDIUM    5% to <20%
HIGH      20% to <50%
VERY_HIGH >=50%
```

## Test-population result

| Risk Band | Customers | Defaults | Avg Predicted PD | Actual Default Rate |
|---|---:|---:|---:|---:|
| LOW | 508 | 18 | 3.32% | 3.54% |
| MEDIUM | 60 | 6 | 7.65% | 10.00% |
| HIGH | 35 | 10 | 30.49% | 28.57% |
| VERY_HIGH | 44 | 35 | 77.82% | 79.55% |

## Interpretation

The model shows clear risk separation:

```text
LOW        -> 3.5% actual default
MEDIUM     -> 10.0%
HIGH       -> 28.6%
VERY_HIGH  -> 79.5%
```

This is easier for business users to consume than raw model probabilities.

---

# 35. Data and Portfolio Monitoring

File:

```text
src/monitoring/01_pd_monitoring.py
```

## Purpose

Create a lightweight monitoring baseline.

Checks include:

```text
missingness
feature distribution snapshots
portfolio size
portfolio default rate
```

## Baseline data-quality result

```text
account_count                  missing = 0.00%
total_credit_limit             missing = 0.00%
entity_utilization             missing = 0.31%
missing_balance_count          missing = 0.00%
current_max_dpd                missing = 0.00%
delinquent_snapshots_30plus    missing = 0.00%
ever_90_dpd                    missing = 0.00%
```

## Baseline feature snapshot

```text
account_count mean ≈ 2.52
total_credit_limit mean ≈ 37,665
entity_utilization mean ≈ 42.09%
missing_balance_count mean ≈ 0.038
current_max_dpd mean ≈ 5.99
delinquent_snapshots_30plus mean ≈ 1.46
ever_90_dpd mean ≈ 6.34%
```

## Portfolio baseline

```text
Entities     = 3,231
Default rate = 10.68%
```

## Why this matters

Future scoring cohorts can be compared against this baseline.

Examples:

```text
utilization jumps from 42% to 65%
-> customer mix / behavior may have shifted

missing balance jumps from 1% to 15%
-> likely data pipeline issue

default rate rises from 10.7% to 18%
-> portfolio deterioration may be occurring
```

---

# 36. Model Performance Monitoring

File:

```text
src/monitoring/02_model_performance.py
```

## Purpose

Track whether the model is still separating risk effectively once outcomes are available.

Metrics:

```text
ROC-AUC
PR-AUC
Precision
Recall
Threshold
```

Current held-out result:

```text
ROC-AUC   = 0.863
PR-AUC    = 0.636
Precision = 0.570
Recall    = 0.652
Threshold = 0.20
```

Future warning example:

```text
Launch:
ROC-AUC = 0.86
Recall  = 0.65

Later cohort:
ROC-AUC = 0.68
Recall  = 0.42
```

That would indicate meaningful model degradation.

---

# 37. Vendor Score Table

Raw table:

```text
vendor_scores
```

Columns:

```text
account_id
score_date
vendor_risk_score
vendor_risk_band
```

Example:

```text
A000001 | 2025-01-31 | 640.2 | C
A000002 | 2025-01-31 | 737.6 | B
A000003 | 2025-01-31 | 640.2 | C
A000004 | 2025-01-31 | 515.3 | E
A000005 | 2025-01-31 | 706.7 | B
```

Higher vendor scores correspond to safer bands in this synthetic dataset.

Important:

This is a synthetic vendor score created for the lab.

It is not a real WEX vendor model.

---

# 38. Vendor vs Internal Comparison

File:

```text
src/models/05_vendor_vs_internal.py
```

## Purpose

Compare the internal entity-level PD model with the synthetic vendor score on the same customers and same future-default target.

Because the vendor score is account-level while the internal model is entity-level, the vendor score is first aggregated.

Entity-level vendor score:

```text
AVG(vendor_risk_score)
```

across all accounts linked to the entity.

Since higher vendor score means safer customer, the score is sign-reversed for risk ranking:

```text
vendor_risk = -avg_vendor_score
```

## Fair comparison principle

Both models must be evaluated on:

```text
same customer population
same target
same test split
same metrics
```

Otherwise the comparison is not meaningful.

## Result

Comparison population:

```text
Entities     = 3,231
Default rate = 10.68%
```

Internal model:

```text
ROC-AUC = 0.863
PR-AUC  = 0.636
```

Synthetic vendor score:

```text
ROC-AUC = 0.570
PR-AUC  = 0.128
```

## Interpretation

In this synthetic environment, the internal model provides substantially better risk separation than the vendor score.

This does not prove that internal models are always better than vendor models.

It demonstrates how to benchmark an existing score fairly.

---

# 39. Final Working PD Model

Final working model:

```text
Logistic Regression V2
```

Features:

```text
account_count
total_credit_limit
entity_utilization
missing_balance_count
current_max_dpd
delinquent_snapshots_30plus
ever_90_dpd
```

Primary test metrics:

```text
ROC-AUC   = 0.863
PR-AUC    = 0.636
Precision ≈ 0.57
Recall    ≈ 0.65
Threshold = 0.20
```

Risk-band default rates:

```text
LOW        ≈ 3.5%
MEDIUM     ≈ 10.0%
HIGH       ≈ 28.6%
VERY_HIGH  ≈ 79.5%
```

---

# 40. What We Intentionally Did Not Build

This project intentionally avoided unnecessary complexity.

Not included:

```text
large hyperparameter sweeps
dozens of model types
fake production APIs
complex MLOps infrastructure
deep SHAP analysis
large dashboard layer
full feature-store platform
```

The goal was to focus on realistic day-to-day risk science:

```text
data quality
entity resolution
feature engineering
target design
modeling
thresholding
calibration
risk bands
monitoring
benchmarking
```

---

# 41. Important Technical Caveats

## 41.1 Static account balance limitation

The raw `current_balance` field is not a true historical balance snapshot table.

For this synthetic lab, it is treated as available at the scoring date.

In a production system, exposure features should be explicitly point-in-time.

## 41.2 Historical delinquency includes scoring date

The historical delinquency query uses:

```text
snapshot_date <= 2025-06-30
```

That is acceptable because June 30 information is available at scoring time.

## 41.3 Historical 90-DPD customers can remain eligible

A customer may have been 90-DPD historically but recovered before the scoring date.

Such a customer can remain in the modeling population as long as:

```text
currently_defaulted = 0
```

## 41.4 60-DPD customers can later become 90-DPD

A customer at:

```text
60 DPD on 2025-06-30
```

can validly become a future default if they reach 90-DPD during the performance window.

## 41.5 Random split limitation

The current model uses a stratified random split because all records belong to one as-of-date cohort.

A stronger production validation design would use multiple monthly cohorts and out-of-time testing.

## 41.6 Synthetic vendor model limitation

The vendor score is only a synthetic benchmark.

It should not be interpreted as evidence about any real external vendor.

---

# 42. Recommended Run Order

A clean run sequence is:

```text
1. Create database schema
2. Load raw data
3. Normalize customer identity
4. Generate candidate pairs
5. Score candidate pairs
6. Classify matches
7. Evaluate entity resolution
8. Inspect false negatives
9. Build customer entities
10. Build entity exposure
11. Build delinquency history
12. Build future target
13. Build current delinquency
14. Build PD modeling mart
15. Train baseline logistic model
16. Run threshold analysis
17. Run feature correlation analysis
18. Train simplified logistic V2
19. Check calibration
20. Build risk bands
21. Run data / portfolio monitoring
22. Run model-performance monitoring
23. Compare vendor vs internal model
```

---

# 43. Example Commands

Open the database:

```bash
sqlite3 database/risk_lab.db
```

Load raw data:

```bash
python src/load_raw_data.py
```

Run entity-resolution scripts:

```bash
python src/entity_resolution/01_normalize_customers.py
python src/entity_resolution/02_generate_candidates.py
python src/entity_resolution/03_score_candidates.py
python src/entity_resolution/04_classify_matches.py
python src/entity_resolution/05_evaluate_matches.py
python src/entity_resolution/06_inspect_false_negatives.py
python src/entity_resolution/07_build_entities.py
```

Run model scripts:

```bash
python src/models/01_logistic_pd_baseline.py
python src/models/02_threshold_analysis.py
python src/models/03_feature_correlation.py
python src/models/04_logistic_pd_v2.py
python src/models/05_vendor_vs_internal.py
```

Run monitoring:

```bash
python src/monitoring/01_pd_monitoring.py
python src/monitoring/02_model_performance.py
```

---

# 44. Core Business Story

The project can be summarized as:

> I started with messy customer- and account-level data, performed data-quality validation, resolved duplicate customer identities conservatively, and created a reliable entity-level view of exposure and delinquency. I then built a point-in-time 180-day probability-of-default modeling mart, trained an interpretable logistic regression baseline, analyzed thresholds, simplified correlated features, validated calibration, created business-friendly risk bands, and added lightweight monitoring. Finally, I benchmarked the internal model against the existing synthetic vendor score on the same held-out population.

---

# 45. Key Lessons

## Data quality comes before modeling

A strong model cannot fix broken entity relationships.

## Entity resolution can materially affect risk estimates

False merges and false splits can distort exposure and delinquency.

## Point-in-time correctness matters

Features must be available before the prediction date.

## Accuracy is not enough

For an imbalanced default problem, use:

```text
ROC-AUC
PR-AUC
precision
recall
false-positive rate
```

## Thresholds are business decisions

The default 0.50 threshold is not automatically appropriate.

## Simpler models can be better

Removing redundant features improved interpretability and preserved or improved performance.

## Calibration matters in credit risk

A PD should ideally behave like a probability, not just a ranking score.

## Risk bands make the model operational

Business users can act on risk tiers more easily than raw probabilities.

## Monitoring is part of the model

Data quality, feature distributions, portfolio risk, and model performance all need ongoing checks.

## Benchmarking must be fair

Vendor and internal models must be compared on the same population and target.

---

# 46. Final Metrics Snapshot

Entity resolution:

```text
Precision = 1.000
Recall    = 0.952
F1        = 0.975
```

PD modeling population:

```text
Eligible entities = 3,231
Future defaults   = 345
Default rate      = 10.68%
```

Final internal model:

```text
ROC-AUC   = 0.863
PR-AUC    = 0.636
Precision ≈ 0.57
Recall    ≈ 0.65
Threshold = 0.20
```

Risk bands:

```text
LOW        ≈ 3.5% default
MEDIUM     ≈ 10.0%
HIGH       ≈ 28.6%
VERY_HIGH  ≈ 79.5%
```

Synthetic vendor benchmark:

```text
ROC-AUC = 0.570
PR-AUC  = 0.128
```

---

# 47. Suggested GitHub Positioning

A concise repository description:

> End-to-end synthetic credit-risk modernization lab covering data quality, customer entity resolution, point-in-time feature engineering, probability-of-default modeling, threshold selection, calibration, risk segmentation, monitoring, and vendor benchmarking.

Suggested topics:

```text
credit-risk
data-science
entity-resolution
logistic-regression
risk-modeling
model-monitoring
python
sql
sqlite
machine-learning
```

---

# 48. Final Note

This project is intentionally synthetic.

It is designed to demonstrate:

```text
reasoning
workflow design
modeling discipline
risk interpretation
data-quality thinking
production-awareness
```

It should not be represented as real WEX production data, real vendor performance, or actual company logic.

The value of the project is the end-to-end methodology.
