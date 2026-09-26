from __future__ import annotations

from datetime import UTC, datetime
import re
from typing import Any

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _clean_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return normalize_whitespace(text)


def _parse_iso_date(date_str: str) -> datetime | None:
    cleaned = str(date_str or "").strip()
    if not cleaned:
        return None
    try:
        return datetime.strptime(cleaned[:10], "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def format_text_for_embedding(
    title: str,
    authors_joined: str,
    categories_joined: str,
    published: str,
    summary: str,
) -> str:
    return (
        f"Title: {title}\n"
        f"Authors: {authors_joined}\n"
        f"Categories: {categories_joined}\n"
        f"Published: {published}\n"
        f"Summary: {summary}"
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """TODO(student): clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    run_dt = run_date if run_date.tzinfo is not None else run_date.replace(tzinfo=UTC)
    run_day = run_dt.astimezone(UTC).date()

    rows: list[dict[str, Any]] = []
    for record in records:
        paper_id = _clean_text(record.paper_id)
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        if not paper_id or not title or not summary:
            continue

        published_dt = _parse_iso_date(record.published)
        if published_dt is None:
            continue
        updated_dt = _parse_iso_date(record.updated) or published_dt

        published_str = published_dt.date().isoformat()
        updated_str = updated_dt.date().isoformat()
        age_days = max(0, (run_day - published_dt.date()).days)

        authors = [_clean_text(a) for a in (record.authors or []) if _clean_text(a)]
        if not authors:
            authors = ["Unknown Author"]

        categories = [_clean_text(c) for c in (record.categories or []) if _clean_text(c)]
        if not categories:
            categories = ["General"]

        primary_category = _clean_text(record.primary_category) or categories[0]
        authors_joined = compact_join(authors)
        categories_joined = compact_join(categories)
        summary_chars = len(summary)
        abs_url = _clean_text(record.abs_url) or f"https://doi.org/{paper_id}"
        pdf_url = _clean_text(record.pdf_url) or abs_url
        comment = _clean_text(record.comment) or f"Crossref record {paper_id}"

        text_for_embedding = format_text_for_embedding(
            title=title,
            authors_joined=authors_joined,
            categories_joined=categories_joined,
            published=published_str,
            summary=summary,
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_str,
                "updated": updated_str,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "comment": comment,
                "age_days": int(age_days),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": int(summary_chars),
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[
        (df["paper_id"].str.len() > 0)
        & (df["title"].str.len() >= 8)
        & (df["summary_chars"] >= 20)
    ]
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df
