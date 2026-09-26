# Phase 1 Baseline Report

## Source and indexing

| Field | Value |
|---|---|
| `source` | Crossref REST API |
| `query` | agentic retrieval augmented generation large language model |
| `filter` | from-pub-date:2026-03-30,has-abstract:true |
| `raw_records` | 24 |
| `clean_records` | 24 |
| `collection_name` | papers-baseline |

## Baseline metrics

| Metric | Value |
|---|---:|
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |

## Great Expectations quality gate

Overall status: **PASS**

| Expectation | Target | Status | Observed/unexpected |
|---|---|---|---:|
| `expect_table_row_count_to_be_between` | `table` | PASS | 24 |
| `expect_column_values_to_not_be_null` | `paper_id` | PASS | 0 |
| `expect_column_values_to_not_be_null` | `title` | PASS | 0 |
| `expect_column_values_to_not_be_null` | `text_for_embedding` | PASS | 0 |
| `expect_column_values_to_be_unique` | `paper_id` | PASS | 0 |
| `expect_column_value_lengths_to_be_between` | `summary` | PASS | 0 |

## Freshness SLA

| Field | Value |
|---|---:|
| Latest publication | 2026-07-22 |
| Oldest publication | 2026-03-28 |
| Stale rows | 1 / 24 |
| Stale ratio | 0.0417 |
| Threshold | 180 days |
| Status | FRESH |
