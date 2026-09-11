# Entity Resolution Metrics

## Executive summary

The current entity-resolution rules are intentionally **precision-first**. The primary
business risk is incorrectly merging two different customers into one entity, so an
automatic match must be highly reliable. Ambiguous cases are not forced into a match:
they remain available for Risk team review.

## Evaluation results

The evaluation compared the pipeline's predicted duplicate pairs with the held-out
entity-resolution reference truth. The reference file was used only for evaluation,
not for normalization, candidate generation, scoring, or classification.

| Metric | Result |
|---|---:|
| True duplicate pairs in reference data | 982 |
| Predicted `MATCH` pairs | 935 |
| True positives | 935 |
| False positives | 0 |
| False negatives (missed duplicate pairs) | 47 |
| Precision | **100.0%** |
| Recall | **95.2%** |
| F1 score | **97.5%** |

The candidate pipeline evaluated 5,303 record pairs. The resulting decisions were
935 `MATCH`, 2,219 `REVIEW`, and 2,149 `NO_MATCH`. These volumes show that the rules
are conservative: they automatically match only pairs with sufficiently strong
evidence and route uncertain evidence away from automatic merging.

## Risk and operational interpretation

Precision is prioritized over recall because a false positive could place two
different entities under the same customer record. That type of incorrect merge can
contaminate account, application, transaction, payment, and risk histories and is
more damaging than leaving a genuine duplicate unresolved temporarily.

The 47 false negatives are genuine duplicate pairs that were not automatically
matched. They are recall gaps, not evidence that the precision-first approach failed.
Cases involving likely duplicates, inconsistent identity details, typos, shared
contact information, or other ambiguous patterns should be sent to the Risk team
for further review rather than being promoted automatically. Risk reviewers can
validate the relationship and decide whether a controlled merge or rule improvement
is appropriate.

**Recommended control:** retain the current automatic `MATCH` threshold, monitor
false positives as the highest-severity exception, and use Risk team decisions on
`REVIEW` cases and investigated false negatives to guide future rule changes.
