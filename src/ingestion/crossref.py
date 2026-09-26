from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

CROSSREF_WORKS_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_jats_tags(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", text or "")
    return normalize_whitespace(cleaned)


def _extract_date_str(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        block = item.get(key)
        if not isinstance(block, dict):
            continue
        date_parts = block.get("date-parts")
        if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
            parts = date_parts[0]
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            day = int(parts[2]) if len(parts) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
        date_time = block.get("date-time")
        if isinstance(date_time, str) and len(date_time) >= 10:
            return date_time[:10]
    return ""


def _extract_authors(item: dict[str, Any]) -> list[str]:
    raw_authors = item.get("author") or []
    authors: list[str] = []
    for author in raw_authors:
        if not isinstance(author, dict):
            continue
        given = str(author.get("given") or "").strip()
        family = str(author.get("family") or "").strip()
        full_name = normalize_whitespace(f"{given} {family}")
        if not full_name:
            full_name = normalize_whitespace(str(author.get("name") or ""))
        if full_name:
            authors.append(full_name)
    return authors or ["Unknown Author"]


def _extract_pdf_url(item: dict[str, Any], default_url: str) -> str:
    links = item.get("link") or []
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            url = str(link.get("URL") or "").strip()
            content_type = str(link.get("content-type") or "").lower()
            if url and ("pdf" in content_type or url.lower().endswith(".pdf")):
                return url
    return default_url


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """TODO(student): parse Crossref payload thanh list PaperRecord.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    message = payload.get("message") if isinstance(payload, dict) else {}
    items = message.get("items") if isinstance(message, dict) else []
    if not isinstance(items, list):
        return []

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = normalize_whitespace(str(item.get("DOI") or ""))
        raw_titles = item.get("title") or []
        title = ""
        if isinstance(raw_titles, list) and raw_titles:
            title = normalize_whitespace(str(raw_titles[0] or ""))
        elif isinstance(raw_titles, str):
            title = normalize_whitespace(raw_titles)

        summary = _strip_jats_tags(str(item.get("abstract") or ""))
        if not paper_id or not title or not summary:
            continue

        authors = _extract_authors(item)
        raw_subjects = item.get("subject") or item.get("container-title") or []
        categories: list[str] = []
        if isinstance(raw_subjects, list):
            categories = [normalize_whitespace(str(s)) for s in raw_subjects if normalize_whitespace(str(s))]
        elif isinstance(raw_subjects, str) and normalize_whitespace(raw_subjects):
            categories = [normalize_whitespace(raw_subjects)]
        if not categories:
            categories = ["General"]
        primary_category = categories[0]

        published = _extract_date_str(
            item,
            ("published", "published-print", "published-online", "issued", "created"),
        )
        if not published:
            continue
        updated = _extract_date_str(item, ("updated",)) or published

        abs_url = normalize_whitespace(str(item.get("URL") or "")) or f"https://doi.org/{paper_id}"
        pdf_url = _extract_pdf_url(item, abs_url)
        comment = normalize_whitespace(str(item.get("comment") or "")) or f"Crossref record {paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def _fetch_api_payload_with_retry(settings: Settings, max_retries: int = 3) -> dict[str, Any]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "Day10DataObservabilityLab/1.0 (mailto:student@example.edu)",
        "Accept": "application/json",
    }
    retry_statuses = {429, 500, 502, 503, 504}
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = requests.get(CROSSREF_WORKS_URL, params=params, headers=headers, timeout=15)
            if response.status_code in retry_statuses:
                time.sleep(1.5 * (2**attempt))
                continue
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "message" in data:
                return data
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(1.5 * (2**attempt))

    raise RuntimeError(f"Failed to fetch Crossref API after {max_retries} attempts: {last_error}")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """TODO(student): goi source API, luu raw response, parse thanh records.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    raw_response_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    payload: dict[str, Any] | None = None

    if not settings.refresh_source and raw_response_path.exists():
        payload = read_json(raw_response_path)
    else:
        try:
            payload = _fetch_api_payload_with_retry(settings)
            records_try = parse_crossref_payload(payload)
            if not records_try and raw_response_path.exists():
                payload = read_json(raw_response_path)
        except Exception:
            if raw_response_path.exists():
                payload = read_json(raw_response_path)
            elif raw_records_path.exists():
                return load_raw_records(raw_records_path)
            else:
                raise

    write_json(raw_response_path, payload)
    records = parse_crossref_payload(payload)
    if settings.max_results and len(records) > settings.max_results:
        records = records[: settings.max_results]
    write_json(raw_records_path, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    data = read_json(path)
    if isinstance(data, dict) and "message" in data:
        return parse_crossref_payload(data)
    if not isinstance(data, list):
        return []

    records: list[PaperRecord] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        records.append(
            PaperRecord(
                paper_id=str(item["paper_id"]),
                title=str(item["title"]),
                summary=str(item["summary"]),
                authors=list(item.get("authors") or []),
                categories=list(item.get("categories") or []),
                primary_category=str(item.get("primary_category") or "General"),
                published=str(item["published"]),
                updated=str(item.get("updated") or item["published"]),
                abs_url=str(item.get("abs_url") or f"https://doi.org/{item['paper_id']}"),
                pdf_url=str(item.get("pdf_url") or item.get("abs_url") or f"https://doi.org/{item['paper_id']}"),
                comment=str(item.get("comment") or f"Crossref record {item['paper_id']}"),
            )
        )
    return records
