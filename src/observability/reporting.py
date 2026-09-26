from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _metric_rows(metrics: dict[str, Any]) -> list[str]:
    names = (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    return [f"| `{name}` | {_number(metrics.get(name, 'N/A'))} |" for name in names]


def _quality_rows(quality: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for result in quality.get("expectation_results", []):
        config = result.get("expectation_config", {})
        kwargs = config.get("kwargs", {})
        observed = result.get("result", {}).get("observed_value")
        if observed is None:
            observed = result.get("result", {}).get("unexpected_count", "N/A")
        target = kwargs.get("column", "table")
        rows.append(
            f"| `{config.get('type', 'unknown')}` | `{target}` | "
            f"{'PASS' if result.get('success') else 'FAIL'} | {_number(observed)} |"
        )
    return rows or ["| No GX results | - | FAIL | N/A |"]

def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a reproducible Markdown summary for the baseline phase."""
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source and indexing",
        "",
        "| Field | Value |",
        "|---|---|",
        *[f"| `{key}` | {value} |" for key, value in source_summary.items()],
        "",
        "## Baseline metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        *_metric_rows(metrics),
        "",
        "## Great Expectations quality gate",
        "",
        f"Overall status: **{'PASS' if quality.get('success') else 'FAIL'}**",
        "",
        "| Expectation | Target | Status | Observed/unexpected |",
        "|---|---|---|---:|",
        *_quality_rows(quality),
        "",
        "## Freshness SLA",
        "",
        "| Field | Value |",
        "|---|---:|",
        f"| Latest publication | {freshness.get('latest_published', 'N/A')} |",
        f"| Oldest publication | {freshness.get('oldest_published', 'N/A')} |",
        f"| Stale rows | {freshness.get('stale_rows', 'N/A')} / {freshness.get('total_rows', 'N/A')} |",
        f"| Stale ratio | {_number(freshness.get('stale_ratio', 'N/A'))} |",
        f"| Threshold | {freshness.get('threshold_days', 'N/A')} days |",
        f"| Status | {'FRESH' if freshness.get('is_fresh') else 'STALE'} |",
        "",
    ]
    write_text(Path(report_path), "\n".join(lines))


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write the baseline/corrupted/repaired comparison report."""
    metric_names = (
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    metric_rows = []
    for name in metric_names:
        baseline = baseline_metrics.get(name, "N/A")
        corrupted = corrupted_metrics.get(name, "N/A")
        repaired = repaired_metrics.get(name, "N/A")
        delta = (
            float(corrupted) - float(baseline)
            if isinstance(baseline, (int, float)) and isinstance(corrupted, (int, float))
            else "N/A"
        )
        metric_rows.append(
            f"| `{name}` | {_number(baseline)} | {_number(corrupted)} | "
            f"{_number(repaired)} | {_number(delta)} |"
        )

    lines = [
        "# Corruption and Repair Comparison",
        "",
        "## Evaluation metrics",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Corruption delta |",
        "|---|---:|---:|---:|---:|",
        *metric_rows,
        "",
        "## Observability signals",
        "",
        "| Signal | Corrupted | Repaired |",
        "|---|---:|---:|",
        f"| GX quality gate | {'PASS' if corrupted_quality.get('gx_success') else 'FAIL'} | {'PASS' if repaired_quality.get('gx_success') else 'FAIL'} |",
        f"| Overall quality/freshness gate | {'PASS' if corrupted_quality.get('success') else 'FAIL'} | {'PASS' if repaired_quality.get('success') else 'FAIL'} |",
        f"| Freshness | {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE'} | {'FRESH' if repaired_freshness.get('is_fresh') else 'STALE'} |",
        f"| Stale ratio | {_number(corrupted_freshness.get('stale_ratio', 'N/A'))} | {_number(repaired_freshness.get('stale_ratio', 'N/A'))} |",
        f"| Stale rows | {corrupted_freshness.get('stale_rows', 'N/A')} | {repaired_freshness.get('stale_rows', 'N/A')} |",
        "",
        "## Conclusion",
        "",
        "The same fixed evaluation set was used for all three states. The corrupted state records the effect of the six synthetic incidents; the repaired state is rebuilt from the trusted raw snapshot before re-indexing.",
        "",
    ]
    write_text(Path(report_path), "\n".join(lines))
