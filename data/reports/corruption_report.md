# Corruption and Repair Comparison

## Evaluation metrics

| Metric | Baseline | Corrupted | Repaired | Corruption delta |
|---|---:|---:|---:|---:|
| `retrieval_hit_rate` | 1.0000 | 0.7000 | 1.0000 | -0.3000 |
| `mean_token_f1` | 1.0000 | 0.7000 | 1.0000 | -0.3000 |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | -0.3000 |
| `mean_judge_score` | 5 | 3.8000 | 5 | -1.2000 |

## Observability signals

| Signal | Corrupted | Repaired |
|---|---:|---:|
| GX quality gate | FAIL | PASS |
| Overall quality/freshness gate | FAIL | PASS |
| Freshness | STALE | FRESH |
| Stale ratio | 0.5714 | 0.0417 |
| Stale rows | 12 | 1 |

## Conclusion

The same fixed evaluation set was used for all three states. The corrupted state records the effect of the six synthetic incidents; the repaired state is rebuilt from the trusted raw snapshot before re-indexing.
