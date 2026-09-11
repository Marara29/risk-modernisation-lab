# Copilot instructions

## Project overview

This repository is a synthetic commercial credit/fraud risk lab. The active work is the raw data and entity-resolution foundation, not model development. The main project lives in `risk-modernization-lab/` and uses CSV inputs, a SQLite database, Python/pandas scripts, and standalone SQL exploration checks.

The data flow is:

1. `data/raw/*.csv` contains operational source extracts for customer records, accounts, applications, transactions, payments, delinquencies, and vendor scores.
2. `src/load_raw_data.py` loads those CSVs into `database/risk_lab.db`, replacing the corresponding SQLite tables.
3. The numbered scripts under `src/entity_resolution/` form a sequential pipeline:
   - `01_normalize_customers.py` reads `customer_records` and writes normalized identity fields to `customer_identity_normalized`.
   - `02_generate_candidates.py` blocks on normalized phone, email, and address/city/state and writes candidate record pairs to `entity_candidate_pairs`.
   - `03_score_candidates.py` compares candidate pairs and writes evidence flags and weighted scores to `entity_match_scores`.
   - `04_classify_matches.py` applies the current rule-based thresholds and writes `entity_match_decisions` with `MATCH`, `REVIEW`, or `NO_MATCH`.
4. `sql/quality_checks/` contains exploratory SQL for row counts, missingness, anomalies, relationships, and duplicate checks. `sql/schemas/001_raw_tables.sql` documents the intended raw-table schema.

The CSVs and database are intentionally messy: duplicate customer records, inconsistent identity formatting, missing values, outlier limits, negative transactions, and missing merchant categories are part of the exercise. Preserve those signals for investigation rather than silently cleaning them away.

## Build, run, test, and lint

There is no package manifest, build system, automated test suite, or lint configuration in the repository. The runtime expects Python with `pandas`; scripts use only the standard library plus pandas and SQLite.

Run commands from `risk-modernization-lab/`:

```bash
# Rebuild/refresh the raw SQLite tables from data/raw/*.csv
python src/load_raw_data.py

# Run the entity-resolution stages in order
python src/entity_resolution/01_normalize_customers.py
python src/entity_resolution/02_generate_candidates.py
python src/entity_resolution/03_score_candidates.py
python src/entity_resolution/04_classify_matches.py
```

The scripts resolve paths relative to the project directory, so they do not require a particular current working directory, but running them from `risk-modernization-lab/` keeps command output and SQL paths clear. Each stage overwrites its output table with `if_exists="replace"`.

For SQL checks, open `database/risk_lab.db` with any SQLite client and execute either `sql/quality_checks/001_starter_checks.sql` or `sql/quality_checks/002_data_quality_profile.sql`. There is no single-test command because no tests currently exist.

## Repository-specific conventions

- Keep the numbered entity-resolution stages in dependency order. A later stage expects the SQLite table produced by the preceding stage.
- Use the existing `ROOT = Path(__file__).resolve().parents[...]` pattern for file locations and `sqlite3`/pandas for database I/O.
- Treat SQLite tables produced by scripts as pipeline artifacts. Raw loading replaces the seven raw tables, and each entity-resolution stage replaces its own derived table; do not assume derived tables survive a fresh database reload unless the pipeline is rerun.
- Preserve null semantics. In particular, a missing `accounts.current_balance` is not the same as a known zero balance, and missing identity attributes should not be filled with invented values.
- Keep candidate generation separate from match scoring and classification. Blocking determines which pairs are considered; the weighted evidence flags determine scores; the explicit rules determine decisions.
- Existing matching weights are phone `4`, email `3`, address plus city/state `2`, and normalized name `1`. Changes to these weights or classification rules alter the lab’s matching behavior and should be intentional.
- Normalization is deliberately conservative and field-specific: names/text are lowercased and punctuation/extra whitespace removed, phones retain digits, emails are lowercased and trimmed, and addresses apply a small set of street-suffix replacements before cleanup.
- Do not use `data/reference/entity_truth_DO_NOT_USE_FOR_MODELING.csv` for feature engineering, normalization, candidate generation, scoring, or model development. It is reserved for evaluating entity resolution.
- Negative transaction amounts, extreme credit limits, missing balances, and other anomalies are investigation signals. Do not delete, coerce, or impute them without documenting the business interpretation.
- Keep SQL exploration checks read-only. Use `sql/schemas/001_raw_tables.sql` as the schema reference, while recognizing that the loader currently creates/replaces tables from CSV column inference.
