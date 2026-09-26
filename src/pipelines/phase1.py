from __future__ import annotations

from typing import Any

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> dict[str, Any]:
    """Run the reproducible baseline pipeline and return its key artifacts."""
    settings = load_settings()
    raw_records = fetch_source_records(settings)
    clean_df = build_clean_dataframe(raw_records, run_date=now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    # The baseline must pass observability before it is allowed into ChromaDB.
    quality = run_data_quality_checks(clean_df, settings, stage="baseline")
    freshness = build_freshness_report(
        clean_df,
        settings,
        settings.paths.freshness_report,
    )
    if not quality["success"]:
        raise RuntimeError(
            "Baseline data failed the quality gate; ChromaDB indexing was stopped. "
            f"See {quality['report_path']}"
        )

    index = LocalEmbeddingIndex.build(
        clean_df,
        settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_records": len(raw_records),
        "clean_records": len(clean_df),
        "collection_name": index.collection_name,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    demo_answers = []
    for item in evaluation.answers[:3]:
        answer = answer_question(item["question"], settings=settings, index=index)
        demo_answers.append(
            {
                "question": answer.question,
                "answer": answer.answer,
                "retrieved_doc_ids": answer.retrieved_doc_ids,
            }
        )
    write_json(settings.paths.demo_answers, demo_answers)

    result = {
        "source_summary": source_summary,
        "quality": quality,
        "freshness": freshness,
        "metrics": evaluation.summary,
        "collection_name": index.collection_name,
        "report_path": str(settings.paths.baseline_report),
    }
    print(
        "Baseline pipeline completed: "
        f"{len(clean_df)} papers, collection={index.collection_name}, "
        f"retrieval_hit_rate={evaluation.summary['retrieval_hit_rate']:.3f}"
    )
    return result
