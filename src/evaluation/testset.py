from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a deterministic ten-question benchmark covering four QA types."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "published",
        "categories_joined",
    }
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Cannot build test set; missing columns: {', '.join(missing_columns)}")
    if len(df) < 5:
        raise ValueError("At least 5 clean papers are required to build the evaluation set.")

    sample_count = min(10, len(df))
    sample_indices = [round(index * (len(df) - 1) / (sample_count - 1)) for index in range(sample_count)]
    sampled = df.iloc[sample_indices].reset_index(drop=True)
    question_types = (
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    )

    test_set: list[dict[str, Any]] = []
    for position, (_, row) in enumerate(sampled.iterrows(), start=1):
        question_type = question_types[position - 1]
        title = str(row["title"])
        if question_type == "summary":
            question = f"What is the main contribution described in '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))
        elif question_type == "authors":
            question = f"Who authored '{title}'?"
            ground_truth = str(row["authors_joined"])
        elif question_type == "date":
            question = f"When was '{title}' published?"
            ground_truth = str(row["published"])
        else:
            question = f"What categories are assigned to '{title}'?"
            ground_truth = str(row["categories_joined"])

        test_set.append(
            {
                "id": f"qa-{position:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [str(row["paper_id"])],
            }
        )

    write_json(output_path, test_set)
    return test_set
