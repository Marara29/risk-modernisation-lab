# Recovered model scripts

These files reconstruct the missing scripts under `src/models/`:

- `02_threshold_analysis.py`
- `03_feature_correlation.py`
- `04_logistic_pd_v2.py`
- `05_vendor_vs_internal.py`

Copy them into:

```text
risk-modernization-lab/src/models/
```

Then run from the project root:

```bash
python src/models/02_threshold_analysis.py
python src/models/03_feature_correlation.py
python src/models/04_logistic_pd_v2.py
python src/models/05_vendor_vs_internal.py
```

These are reconstructed from the saved project design/results, so minor numeric differences are possible if the original scripts used a different random seed or split implementation.
