"""LLM summarizer with citations. No API key => no fabricated summary."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.guards import validate_summary


def build_prompt(question: str, language: str, chunks: list[dict[str, Any]]) -> str:
    sources = []
    for i, c in enumerate(chunks, start=1):
        sources.append(
            f"[{i}] title={c['title']!r} page={c.get('page')} url={c['url']}\n{c['text']}"
        )
    joined = "\n\n".join(sources)
    return (
        "You are CivicVoice. Answer ONLY from the numbered sources below.\n"
        "Write the answer in the requested language.\n"
        "Cite every claim with [n] matching a source number.\n"
        "Do not tell anyone how to vote. Do not persuade for or against a ballot measure.\n"
        "If the sources are not enough, say what is missing.\n\n"
        f"Language: {language}\n"
        f"Question: {question}\n\n"
        f"Sources:\n{joined}\n"
    )


def summarize_with_llm(
    question: str,
    language: str,
    chunks: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Returns (summary, reject_reason). summary is None if unavailable or rejected."""
    settings = get_settings()
    if not settings.civicvoice_llm_api_key:
        return None, "no_api_key"
    if not chunks:
        return None, "no_chunks"
    if not settings.civicvoice_llm_base_url or not settings.civicvoice_llm_model:
        return None, "llm_not_configured"

    prompt = build_prompt(question, language, chunks)
    url = settings.civicvoice_llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.civicvoice_llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.civicvoice_llm_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "You write cited civic summaries only."},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        summary = data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None, "llm_error"

    ok, reason = validate_summary(summary, chunks)
    if not ok:
        return None, reason
    return summary, None


def find_example_answer(question: str, language: str, city: str | None) -> dict[str, Any] | None:
    from app.db import get_connection

    q = question.strip().lower()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, question, language, answer, chunk_ids, city
            FROM example_answers
            WHERE lower(language) = lower(%s)
              AND (%s::text IS NULL OR city IS NULL OR lower(city) = lower(%s))
            """,
            (language, city, city),
        ).fetchall()

    for row in rows:
        if row["question"].strip().lower() == q:
            return row
        # soft match: example question contained in user question or vice versa
        eq = row["question"].strip().lower()
        if eq in q or q in eq:
            return row
    return None
