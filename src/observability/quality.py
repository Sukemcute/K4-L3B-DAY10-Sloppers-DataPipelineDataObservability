from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


CRITICAL_COLUMNS = ("paper_id", "title", "text_for_embedding")
STALE_RATIO_LIMIT = 0.25


def evaluate_freshness_sla(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    """Evaluate whether no more than 25% of papers exceed the age SLA."""
    total_rows = int(len(df))
    if "age_days" not in df.columns:
        return {
            "threshold_days": int(settings.freshness_threshold_days),
            "stale_ratio_limit": STALE_RATIO_LIMIT,
            "stale_rows": 0,
            "total_rows": total_rows,
            "stale_ratio": 0.0,
            "is_fresh": False,
            "error": "Missing required freshness column: age_days",
        }

    ages = pd.to_numeric(df["age_days"], errors="coerce")
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 0.0
    return {
        "threshold_days": int(settings.freshness_threshold_days),
        "stale_ratio_limit": STALE_RATIO_LIMIT,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": float(stale_ratio),
        "is_fresh": bool(stale_ratio <= STALE_RATIO_LIMIT),
    }


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    stage: str,
) -> dict[str, Any]:
    """Run the GX quality gate and freshness SLA, then persist its result."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    required_columns = {*CRITICAL_COLUMNS, "summary"}
    missing_columns = sorted(required_columns.difference(df.columns))
    expectation_results: list[dict[str, Any]] = []

    if not missing_columns:
        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name="papers_source")
        data_asset = data_source.add_dataframe_asset(name="papers_asset")
        batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})

        expectations = [
            gx.expectations.ExpectTableRowCountToBeBetween(
                min_value=5,
                max_value=5000,
            ),
            *[
                gx.expectations.ExpectColumnValuesToNotBeNull(column=column)
                for column in CRITICAL_COLUMNS
            ],
            gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"),
            gx.expectations.ExpectColumnValueLengthsToBeBetween(
                column="summary",
                min_value=30,
            ),
        ]
        expectation_results = [
            batch.validate(expectation).to_json_dict() for expectation in expectations
        ]

    gx_success = bool(
        not missing_columns
        and expectation_results
        and all(result.get("success", False) for result in expectation_results)
    )
    freshness = evaluate_freshness_sla(df, settings)
    payload: dict[str, Any] = {
        "stage": stage,
        "success": bool(gx_success and freshness["is_fresh"]),
        "gx_success": gx_success,
        "is_fresh": freshness["is_fresh"],
        "stale_ratio": freshness["stale_ratio"],
        "missing_columns": missing_columns,
        "expectation_results": expectation_results,
        "freshness": freshness,
    }

    report_path = settings.paths.quality_dir / f"{safe_slug(stage)}_quality_report.json"
    write_json(report_path, payload)
    payload["report_path"] = str(report_path)
    return payload


def build_freshness_report(
    df: pd.DataFrame,
    settings: Settings,
    report_path: str | Path,
) -> dict[str, Any]:
    """Build and persist a standalone freshness report."""
    freshness = evaluate_freshness_sla(df, settings)
    published = (
        pd.to_datetime(df["published"], errors="coerce", utc=True)
        if "published" in df.columns
        else pd.Series(dtype="datetime64[ns, UTC]")
    )
    valid_published = published.dropna()

    payload = {
        "latest_published": (
            valid_published.max().date().isoformat() if not valid_published.empty else None
        ),
        "oldest_published": (
            valid_published.min().date().isoformat() if not valid_published.empty else None
        ),
        **freshness,
    }
    write_json(Path(report_path), payload)
    return payload
