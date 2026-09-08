# Risk Modernization Lab

A synthetic commercial credit/fraud risk environment designed to simulate a messy legacy setup:
fragmented customer records, account-level legacy vendor scores, no prebuilt modeling mart,
data-quality issues, entity-resolution challenges, and raw operational tables.

## Current module: Raw environment + exploration

### Dataset sizes
- customer_records: 4,446
- accounts: 9,060
- applications: 9,060
- transactions: 241,122
- payments: 179,885
- delinquencies: 184,588
- vendor_scores: 9,060

## Intentionally messy elements
- Duplicate customer records representing the same real entity
- Inconsistent phone/name/address formats
- Some missing identifying attributes
- Missing account balances
- A few extreme credit limits
- Negative transaction amounts representing possible reversals/refunds
- Missing merchant categories
- Legacy vendor scores that work at the account level but ignore entity-level exposure

## Important rule
Do not use `data/reference/entity_truth_DO_NOT_USE_FOR_MODELING.csv` for feature engineering.
It is synthetic ground truth reserved for evaluating entity resolution later.

## Suggested first actions
1. Open `database/risk_lab.db` in SQLite.
2. Run `sql/quality_checks/001_starter_checks.sql`.
3. Inspect table grain and relationships.
4. Document what looks suspicious before fixing anything.
5. Do NOT build a machine-learning model yet.
