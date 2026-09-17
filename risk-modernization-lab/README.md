# Risk Modernization Lab

End-to-end synthetic credit-risk modernization project covering data quality, customer entity resolution, point-in-time feature engineering, probability-of-default modeling, threshold selection, calibration, risk segmentation, monitoring, and vendor benchmarking.

> This repository uses synthetic data. It does not contain real WEX data, real vendor model results, or proprietary production logic.

## Project Goal

The project starts with raw operational-style customer and account data rather than a clean modeling table.

The workflow is:

```text
Raw data
→ Data quality checks
→ Customer entity resolution
→ Entity-level feature engineering
→ Point-in-time PD modeling mart
→ Logistic regression baseline
→ Threshold analysis
→ Feature simplification
→ Calibration
→ Risk bands
→ Monitoring
→ Vendor benchmark
```

The goal is to show the full risk-science workflow, not just model training.

## Repository Structure

```text
risk-modernization-lab/
├── data/
│   └── reference/
│       └── entity_truth_DO_NOT_USE_FOR_MODELING.csv
├── database/
│   └── risk_lab.db
├── sql/
│   ├── schemas/
│   │   └── 001_raw_tables.sql
│   └── features/
│       ├── 001_entity_exposure.sql
│       ├── 002_entity_delinquency.sql
│       ├── 003_default_target.sql
│       ├── 004_current_delinquency.sql
│       └── 005_pd_modeling_mart.sql
├── src/
│   ├── load_raw_data.py
│   ├── entity_resolution/
│   │   ├── 01_normalize_customers.py
│   │   ├── 02_generate_candidates.py
│   │   ├── 03_score_candidates.py
│   │   ├── 04_classify_matches.py
│   │   ├── 05_evaluate_matches.py
│   │   ├── 06_inspect_false_negatives.py
│   │   └── 07_build_entities.py
│   ├── models/
│   │   ├── 01_logistic_pd_baseline.py
│   │   ├── 02_threshold_analysis.py
│   │   ├── 03_feature_correlation.py
│   │   ├── 04_logistic_pd_v2.py
│   │   └── 05_vendor_vs_internal.py
│   └── monitoring/
│       ├── 01_pd_monitoring.py
│       └── 02_model_performance.py
├── PROJECT_WALKTHROUGH.md
└── README.md
```

## Data

Synthetic raw tables:

- `customer_records`
- `accounts`
- `applications`
- `transactions`
- `payments`
- `delinquencies`
- `vendor_scores`

Loaded row counts:

| Table | Rows |
|---|---:|
| customer_records | 4,446 |
| accounts | 9,060 |
| applications | 9,060 |
| transactions | 241,122 |
| payments | 179,885 |
| delinquencies | 184,588 |
| vendor_scores | 9,060 |

## 1. Data Quality

Before modeling, the project checks:

- missing identity fields,
- account balance/limit issues,
- transaction anomalies,
- referential integrity,
- duplicate IDs,
- orphan records.

The main modeling-readiness issue was customer identity rather than relational integrity.

## 2. Entity Resolution

Customer records are normalized and linked using evidence from:

- phone,
- email,
- address,
- name.

The matching policy intentionally prioritizes precision to avoid false customer merges.

Final entity-resolution performance:

```text
Precision = 1.000
Recall    = 0.952
F1        = 0.975
```

Source records:

```text
4,446 customer records
→ 3,545 resolved entities
```

## 3. Entity-Level Features

The project aggregates account-level information to the resolved customer entity.

Examples:

- account count,
- total credit limit,
- total balance,
- entity utilization,
- current delinquency,
- historical max DPD,
- repeated 30+ DPD snapshots,
- severe delinquency history.

## 4. Point-in-Time PD Target

Scoring date:

```text
2025-06-30
```

Observation data:

```text
information available on or before 2025-06-30
```

Performance window:

```text
2025-07-01 through 2025-12-31
```

Target:

```text
default_180d = 1
if any linked account reaches 90+ DPD during the future window
```

Customers already at 90+ DPD on the scoring date are excluded from the PD population.

Final modeling mart:

```text
Eligible entities = 3,231
Future defaults   = 345
Default rate      = 10.68%
```

## 5. Baseline PD Model

Model:

```text
Logistic Regression
```

Pipeline:

```text
Median imputation
→ StandardScaler
→ LogisticRegression
```

Baseline validation performance:

```text
ROC-AUC = 0.822
PR-AUC  = 0.570
```

## 6. Threshold Selection

Thresholds from `0.50` to `0.10` were tested.

A threshold of:

```text
0.20
```

was selected as a practical validation tradeoff between default capture and false positives.

Held-out test result:

```text
Precision ≈ 57%
Recall    ≈ 65–67%
```

The model catches roughly two-thirds of future defaults.

## 7. Feature Simplification

Correlation analysis revealed redundant delinquency and exposure variables.

The model was reduced from 16 features to 7:

```text
account_count
total_credit_limit
entity_utilization
missing_balance_count
current_max_dpd
delinquent_snapshots_30plus
ever_90_dpd
```

The simpler model performed better while remaining easier to interpret.

Final held-out performance:

```text
ROC-AUC   = 0.863
PR-AUC    = 0.636
Precision = 0.570
Recall    = 0.652
Threshold = 0.20
```

## 8. Calibration and Risk Bands

Brier score:

```text
0.0583
```

Risk bands on the held-out population:

| Risk Band | Customers | Defaults | Avg Predicted PD | Actual Default Rate |
|---|---:|---:|---:|---:|
| LOW | 508 | 18 | 3.32% | 3.54% |
| MEDIUM | 60 | 6 | 7.65% | 10.00% |
| HIGH | 35 | 10 | 30.49% | 28.57% |
| VERY_HIGH | 44 | 35 | 77.82% | 79.55% |

Observed default rates rise clearly as model risk increases.

## 9. Monitoring

Monitoring covers:

### Data quality
- missing values,
- feature availability.

### Feature/portfolio monitoring
- utilization,
- total exposure,
- delinquency levels,
- portfolio default rate.

### Model performance
- ROC-AUC,
- PR-AUC,
- precision,
- recall.

Baseline monitored performance:

```text
ROC-AUC   = 0.863
PR-AUC    = 0.636
Precision = 0.570
Recall    = 0.652
```

## 10. Vendor vs Internal Benchmark

The synthetic vendor score is account-level, so it is aggregated to the entity level before comparison.

Both scores are evaluated on:

- the same population,
- the same target,
- the same held-out test sample,
- the same metrics.

Results:

| Model | ROC-AUC | PR-AUC |
|---|---:|---:|
| Internal PD model | 0.863 | 0.636 |
| Synthetic vendor score | 0.570 | 0.128 |

In this synthetic benchmark, the internal model provides substantially stronger risk separation.

This result should not be generalized to real vendor models.

## Running the Project

Open the database:

```bash
sqlite3 database/risk_lab.db
```

Load data:

```bash
python src/load_raw_data.py
```

Entity resolution:

```bash
python src/entity_resolution/01_normalize_customers.py
python src/entity_resolution/02_generate_candidates.py
python src/entity_resolution/03_score_candidates.py
python src/entity_resolution/04_classify_matches.py
python src/entity_resolution/05_evaluate_matches.py
python src/entity_resolution/06_inspect_false_negatives.py
python src/entity_resolution/07_build_entities.py
```

Modeling:

```bash
python src/models/01_logistic_pd_baseline.py
python src/models/02_threshold_analysis.py
python src/models/03_feature_correlation.py
python src/models/04_logistic_pd_v2.py
python src/models/05_vendor_vs_internal.py
```

Monitoring:

```bash
python src/monitoring/01_pd_monitoring.py
python src/monitoring/02_model_performance.py
```

## Detailed Walkthrough

For the full step-by-step explanation of every schema, script, design choice, metric, result, and limitation, see:

```text
PROJECT_WALKTHROUGH.md
```

## Key Lessons

- Data quality comes before modeling.
- Entity resolution can materially change customer-level risk.
- Point-in-time feature design is required to avoid leakage.
- Accuracy alone is not appropriate for imbalanced default problems.
- Model thresholds should be tied to business tradeoffs.
- Simpler feature sets can outperform redundant ones.
- Calibration matters when model output is interpreted as PD.
- Risk bands make model output easier to operationalize.
- Monitoring is part of the model lifecycle.
- Vendor benchmarks must use the same population and target.

## Limitations

This is a synthetic lab.

Important limitations include:

- account balances are not modeled as a full historical snapshot table,
- the current experiment uses a single scoring-date cohort,
- the train/validation/test split is stratified rather than out-of-time,
- the vendor score is synthetic,
- the repository does not represent real WEX production logic or proprietary data.

A stronger production implementation would use multiple monthly cohorts, explicit point-in-time exposure snapshots, out-of-time validation, and governed feature/model pipelines.
