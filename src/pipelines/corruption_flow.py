from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> dict[str, Any]:
    """Run corruption, observe degradation, repair from raw data, and compare."""
    settings = load_settings()
    required_baseline_artifacts = [
        settings.paths.clean_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.raw_records_json,
    ]
    missing = [str(path) for path in required_baseline_artifacts if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Run script/run_phase1.py first. Missing baseline artifacts: " + ", ".join(missing)
        )

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_df = pd.read_json(settings.paths.clean_json)
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(
        settings.paths.corrupted_clean_json,
        corrupted_df.to_dict(orient="records"),
    )

    corrupted_quality = run_data_quality_checks(
        corrupted_df,
        settings,
        stage="corrupted",
    )
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        settings.paths.quality_dir / "corrupted_freshness_report.json",
    )

    # This collection is intentionally built even after a failed gate so the
    # controlled experiment can quantify downstream retrieval degradation.
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(
        settings.paths.repaired_clean_json,
        repaired_df.to_dict(orient="records"),
    )
    repaired_quality = run_data_quality_checks(
        repaired_df,
        settings,
        stage="repaired",
    )
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        settings.paths.quality_dir / "repaired_freshness_report.json",
    )
    if not repaired_quality["success"]:
        raise RuntimeError(
            "Repaired data still failed the quality gate; repaired indexing was stopped. "
            f"See {repaired_quality['report_path']}"
        )

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_evaluation.summary,
        repaired_metrics=repaired_evaluation.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    result = {
        "baseline_metrics": baseline_metrics,
        "corrupted_metrics": corrupted_evaluation.summary,
        "repaired_metrics": repaired_evaluation.summary,
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_freshness": corrupted_freshness,
        "repaired_freshness": repaired_freshness,
        "report_path": str(settings.paths.comparison_report),
    }
    print(
        "Corruption flow completed: "
        f"corrupted_quality={corrupted_quality['success']}, "
        f"repaired_quality={repaired_quality['success']}"
    )
    return result
