from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import great_expectations as gx
from great_expectations import expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import ensure_parent, safe_slug, write_json


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Evaluate data freshness SLA based on paper age (age_days).
    
    Rule:
    - Stale paper: age_days > settings.freshness_threshold_days (180 days).
    - If ratio of stale papers exceeds 25%, flag is_fresh = False.
    """
    total_rows = len(df)
    threshold = getattr(settings, "freshness_threshold_days", 180)
    
    if total_rows == 0:
        return {
            "total_rows": 0,
            "freshness_threshold_days": threshold,
            "stale_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": True,
            "latest_published": None,
            "oldest_published": None,
            "min_age_days": None,
            "max_age_days": None,
        }

    has_age = "age_days" in df.columns
    if has_age:
        age_series = pd.to_numeric(df["age_days"], errors="coerce").fillna(0)
        stale_rows = int((age_series > threshold).sum())
        min_age = int(age_series.min()) if not age_series.empty else 0
        max_age = int(age_series.max()) if not age_series.empty else 0
    else:
        stale_rows = 0
        min_age = 0
        max_age = 0

    stale_ratio = float(stale_rows / total_rows) if total_rows > 0 else 0.0
    is_fresh = bool(stale_ratio <= 0.25)

    published_series = df.get("published", pd.Series([], dtype=str)).dropna().astype(str)
    latest_pub = str(published_series.max()) if not published_series.empty else None
    oldest_pub = str(published_series.min()) if not published_series.empty else None

    return {
        "total_rows": total_rows,
        "freshness_threshold_days": threshold,
        "stale_rows": stale_rows,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": is_fresh,
        "latest_published": latest_pub,
        "oldest_published": oldest_pub,
        "min_age_days": min_age,
        "max_age_days": max_age,
    }


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | None = None) -> dict[str, Any]:
    """Generate and persist the freshness monitoring report."""
    report = evaluate_freshness_sla(df, settings)
    target_path = report_path or settings.paths.freshness_report
    write_json(target_path, report)
    return report


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Execute Great Expectations 1.x Ephemeral Quality Gate & Freshness SLA checks.

    4 Mandatory Expectations:
    1. ExpectTableRowCountToBeBetween: 5 to 5000 rows.
    2. ExpectColumnValuesToNotBeNull: paper_id, title, text_for_embedding.
    3. ExpectColumnValuesToBeUnique: paper_id.
    4. ExpectColumnValueLengthsToBeBetween: summary >= 30 chars.
    """
    clean_name = safe_slug(report_name)
    context = gx.get_context(mode="ephemeral")

    source_name = f"papers_source_{clean_name}"
    asset_name = f"papers_asset_{clean_name}"
    suite_name = f"papers_suite_{clean_name}"

    data_source = context.data_sources.add_pandas(name=source_name)
    data_asset = data_source.add_dataframe_asset(name=asset_name)
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name=suite_name)

    # 1. Row count between 5 and 5000
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))

    # 2. Key columns must not be null
    for col in ["paper_id", "title", "text_for_embedding"]:
        if col in df.columns:
            suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=col))

    # 3. Unique paper_id
    if "paper_id" in df.columns:
        suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))

    # 4. Summary length >= 30 chars
    if "summary" in df.columns:
        suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    # Validate batch against expectation suite
    val_results = batch.validate(suite)
    gx_success = bool(val_results.success)

    # Freshness check
    freshness = evaluate_freshness_sla(df, settings)
    is_fresh = bool(freshness["is_fresh"])

    overall_success = bool(gx_success and is_fresh)

    # Convert validation results to serializable dictionary
    raw_gx_dict = val_results.to_json_dict()
    statistics = raw_gx_dict.get("statistics", {})

    report_payload: dict[str, Any] = {
        "report_name": report_name,
        "timestamp": datetime.now(UTC).isoformat(),
        "success": overall_success,
        "gx_success": gx_success,
        "is_fresh": is_fresh,
        "total_expectations": statistics.get("evaluated_expectations", len(suite.expectations)),
        "passed_expectations": statistics.get("successful_expectations", 0),
        "failed_expectations": statistics.get("unsuccessful_expectations", 0),
        "freshness": freshness,
        "gx_statistics": statistics,
    }

    # Determine output path
    if report_name.lower() in {"baseline", "phase1"}:
        out_path = settings.paths.baseline_quality_report
    elif report_name.lower() in {"corrupted", "dirty"}:
        out_path = settings.paths.corrupted_quality_report
    else:
        out_path = settings.paths.quality_dir / f"{clean_name}_quality_report.json"

    write_json(out_path, report_payload)
    build_freshness_report(df, settings, settings.paths.freshness_report)

    return report_payload
