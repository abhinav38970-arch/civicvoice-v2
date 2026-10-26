from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.config import SUPPORTED_LANGUAGES, get_settings
from app.redis_client import get_redis
from app.retriever import retrieve_chunks
from app.summarizer import find_example_answer, summarize_with_llm

router = APIRouter(prefix="/api", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: str = "en"


def _cache_key(question: str, language: str, city: str) -> str:
    raw = f"{city}|{language}|{question.strip().lower()}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"ask:{digest}"


def _rate_limit(user_id: str) -> None:
    settings = get_settings()
    r = get_redis()
    key = f"ask_rate:{user_id}"
    count = int(r.incr(key))
    if count == 1:
        r.expire(key, settings.ask_rate_window_seconds)
    if count > settings.ask_rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many questions. Please wait a minute and try again.",
        )


def _citations_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for i, c in enumerate(chunks, start=1):
        out.append(
            {
                "index": i,
                "chunk_id": c["chunk_id"],
                "document_id": c["document_id"],
                "title": c["title"],
                "url": c["url"],
                "page": c["page"],
                "text": c["text"],
                "doc_type": c["doc_type"],
                "source_name": c["source_name"],
            }
        )
    return out


@router.post("/ask")
def ask(
    body: AskRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    language = body.language.lower().strip()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Use one of: {', '.join(SUPPORTED_LANGUAGES)}",
        )

    _rate_limit(str(user["id"]))
    city = user["city"]
    settings = get_settings()
    r = get_redis()
    cache_key = _cache_key(question, language, city)

    cached = r.get(cache_key)
    if cached:
        payload = json.loads(cached)
        payload["cached"] = True
        return payload

    # Pre-checked demo answers (no LLM required)
    example = find_example_answer(question, language, city)
    if example is not None:
        chunks = retrieve_chunks(question, city=city, limit=8)
        # Prefer chunks linked on the example if present
        payload = {
            "question": question,
            "language": language,
            "city": city,
            "summary": example["answer"],
            "summary_available": True,
            "source": "example",
            "reject_reason": None,
            "message": None,
            "citations": _citations_from_chunks(chunks),
            "cached": False,
        }
        r.setex(cache_key, settings.ask_cache_ttl_seconds, json.dumps(payload))
        return payload

    chunks = retrieve_chunks(question, city=city, limit=8)
    summary, reject_reason = summarize_with_llm(question, language, chunks)

    if summary:
        payload = {
            "question": question,
            "language": language,
            "city": city,
            "summary": summary,
            "summary_available": True,
            "source": "llm",
            "reject_reason": None,
            "message": None,
            "citations": _citations_from_chunks(chunks),
            "cached": False,
        }
    else:
        # Architecture: never invent a summary without a key / if checks fail
        message = (
            "A summary is not available. Here are the relevant document pieces."
        )
        if reject_reason == "ballot_persuasion":
            message = (
                "The generated summary was blocked because it tried to persuade "
                "about a ballot. Showing source pieces instead."
            )
        elif reject_reason == "ungrounded_citations":
            message = (
                "The generated summary was blocked because citations were not grounded. "
                "Showing source pieces instead."
            )

        payload = {
            "question": question,
            "language": language,
            "city": city,
            "summary": None,
            "summary_available": False,
            "source": "documents",
            "reject_reason": reject_reason,
            "message": message,
            "citations": _citations_from_chunks(chunks),
            "cached": False,
        }

    r.setex(cache_key, settings.ask_cache_ttl_seconds, json.dumps(payload))
    return payload
