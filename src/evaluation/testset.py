from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str | None = None) -> list[dict[str, Any]]:
    """Build a standardized benchmark evaluation test set across 4 business groups:
    - summary
    - authors
    - date
    - categories

    Each test case includes:
    - id: Unique test identifier
    - question_type: 'summary' | 'authors' | 'date' | 'categories'
    - question: Question text containing the exact paper title in single quotes
    - ground_truth: Expected factual answer
    - ground_truth_doc_ids: List of ground truth paper IDs (DOIs)
    """
    if len(df) < 4:
        raise ValueError(f"Need at least 4 documents to build a diverse test set, got {len(df)}.")

    records = df.to_dict(orient="records")
    total_docs = len(records)
    test_set: list[dict[str, Any]] = []

    # Distribution of 10 questions across 4 categories:
    # 3 summary, 3 authors, 2 date, 2 categories
    plan = [
        ("summary", 0 % total_docs),
        ("authors", 1 % total_docs),
        ("date", 2 % total_docs),
        ("categories", 3 % total_docs),
        ("summary", 4 % total_docs),
        ("authors", 5 % total_docs),
        ("date", 6 % total_docs),
        ("categories", 7 % total_docs),
        ("summary", 8 % total_docs),
        ("authors", 9 % total_docs),
    ]

    for index, (q_type, doc_idx) in enumerate(plan, start=1):
        doc = records[doc_idx]
        title = doc["title"]
        paper_id = doc["paper_id"]

        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(doc["summary"])
        elif q_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = doc["authors_joined"]
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(doc["published"])
        elif q_type == "categories":
            question = f"What categories does the paper '{title}' belong to?"
            ground_truth = doc["categories_joined"]
        else:
            question = f"Tell me about the paper '{title}'."
            ground_truth = doc["summary"]

        test_set.append(
            {
                "id": f"eval_q_{index:02d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    if output_path:
        write_json(Path(output_path), test_set)

    return test_set
