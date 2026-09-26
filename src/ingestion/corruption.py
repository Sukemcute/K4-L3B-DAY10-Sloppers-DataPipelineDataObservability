from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import now_utc, write_json
from ingestion.cleaning import format_text_for_embedding


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """TODO(student): simulate nhieu dang data corruption.

    Pseudo-code:
    1. Drop mot so latest records.
    2. Blank summary o mot so dong.
    3. Inject noise vao text.
    4. Lam title bi truncate.
    5. Lam published date cu di.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    if df.empty:
        write_json(Path(output_log_path), {"initial_rows": 0, "final_rows": 0, "scenarios": []})
        return df.copy()

    work_df = df.copy()
    work_df["published_dt"] = pd.to_datetime(work_df["published"], errors="coerce")
    work_df = work_df.sort_values(by=["published_dt", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    initial_rows = len(work_df)

    # 1. Drop latest records (20% newest papers)
    drop_count = max(1, int(round(initial_rows * 0.20)))
    dropped_ids = work_df.iloc[:drop_count]["paper_id"].astype(str).tolist()
    work_df = work_df.iloc[drop_count:].reset_index(drop=True)

    remaining = len(work_df)

    # 2. Blank summary on a subset of rows
    blank_indices = [i for i in (0, 1, 2, 3) if i < remaining]
    blank_ids = work_df.loc[blank_indices, "paper_id"].astype(str).tolist()
    work_df.loc[blank_indices, "summary"] = ""

    # 3. Inject noise into summary on another subset of rows
    noise_token = "@@@###$$$ NOISE_CORRUPTED_PAYLOAD_999 %%%^^^&&&"
    noise_indices = [i for i in (4, 5, 6, 7) if i < remaining]
    noise_ids = work_df.loc[noise_indices, "paper_id"].astype(str).tolist()
    for idx in noise_indices:
        work_df.at[idx, "summary"] = f"{noise_token} [GARBAGE_VECTOR_DRIFT] {noise_token}."

    # 4. Truncate title (< 8 chars) on a subset of rows
    trunc_indices = [i for i in (0, 2, 4, 8, 9) if i < remaining]
    trunc_ids = work_df.loc[trunc_indices, "paper_id"].astype(str).tolist()
    for idx in trunc_indices:
        raw_title = str(work_df.at[idx, "title"] or "")
        work_df.at[idx, "title"] = raw_title[:5].strip() or "BadTi"

    # 5. Stale date (shift published date back by 400 days so age_days > 180 exceeds 25% SLA)
    stale_count = max(7, int(round(remaining * 0.45)))
    stale_indices = list(range(min(stale_count, remaining)))
    stale_ids = work_df.loc[stale_indices, "paper_id"].astype(str).tolist()
    for idx in stale_indices:
        pub_dt = work_df.at[idx, "published_dt"]
        if pd.notna(pub_dt):
            old_date = (pub_dt - timedelta(days=400)).strftime("%Y-%m-%d")
        else:
            old_date = "2024-01-15"
        work_df.at[idx, "published"] = old_date
        current_age = int(work_df.at[idx, "age_days"]) if "age_days" in work_df.columns else 100
        work_df.at[idx, "age_days"] = current_age + 400

    work_df = work_df.drop(columns=["published_dt"])

    # 6. Add duplicate rows
    dup_indices = [i for i in (0, 1) if i < len(work_df)]
    dup_rows = work_df.iloc[dup_indices].copy()
    dup_ids = dup_rows["paper_id"].astype(str).tolist()
    work_df = pd.concat([work_df, dup_rows], ignore_index=True)

    # 7. Rebuild summary_chars and text_for_embedding
    work_df["summary"] = work_df["summary"].fillna("").astype(str)
    work_df["title"] = work_df["title"].fillna("").astype(str)
    work_df["published"] = work_df["published"].fillna("").astype(str).str.slice(0, 10)
    work_df["summary_chars"] = work_df["summary"].str.len()
    work_df["text_for_embedding"] = [
        format_text_for_embedding(
            title=str(row["title"]),
            authors_joined=str(row.get("authors_joined") or ""),
            categories_joined=str(row.get("categories_joined") or ""),
            published=str(row["published"]),
            summary=str(row["summary"]),
        )
        for _, row in work_df.iterrows()
    ]

    # 8. Write corruption log
    scenarios: list[dict[str, Any]] = [
        {
            "scenario": "drop_latest_records",
            "description": "Drop 20% of the most recently published records.",
            "affected_count": len(dropped_ids),
            "affected_paper_ids": dropped_ids,
            "parameters": {"drop_ratio": 0.20},
        },
        {
            "scenario": "blank_summary",
            "description": "Set summary to empty string on selected records.",
            "affected_count": len(blank_ids),
            "affected_paper_ids": blank_ids,
            "parameters": {"replacement": ""},
        },
        {
            "scenario": "inject_noise",
            "description": "Inject non-semantic noise tokens into summary text.",
            "affected_count": len(noise_ids),
            "affected_paper_ids": noise_ids,
            "parameters": {"noise_token": noise_token},
        },
        {
            "scenario": "truncate_title",
            "description": "Truncate paper titles to fewer than 8 characters.",
            "affected_count": len(trunc_ids),
            "affected_paper_ids": trunc_ids,
            "parameters": {"max_length": 5},
        },
        {
            "scenario": "stale_date",
            "description": "Shift published dates back by 400 days to violate the 180-day Freshness SLA (>25% stale).",
            "affected_count": len(stale_ids),
            "affected_paper_ids": stale_ids,
            "parameters": {"shift_days": 400, "freshness_threshold_days": 180},
        },
        {
            "scenario": "duplicate_rows",
            "description": "Append duplicate records violating paper_id uniqueness.",
            "affected_count": len(dup_ids),
            "affected_paper_ids": dup_ids,
            "parameters": {"duplicated_rows": len(dup_ids)},
        },
    ]

    log_payload: dict[str, Any] = {
        "corrupted_at": now_utc().isoformat(),
        "initial_rows": initial_rows,
        "final_rows": int(len(work_df)),
        "total_scenarios": len(scenarios),
        "scenarios": scenarios,
    }
    if output_log_path is not None:
        write_json(Path(output_log_path), log_payload)

    return work_df
