"""Safety checks before returning an Ask summary."""

from __future__ import annotations

import re
from typing import Any

# Soft persuasion phrases — ballot answers must stay informational.
_PERSUASIVE = re.compile(
    r"\b("
    r"you should vote|vote\s+yes|vote\s+no|vote for|vote against|"
    r"i recommend|we recommend|support this measure|oppose this measure|"
    r"cast your ballot for|the right choice|must vote"
    r")\b",
    re.IGNORECASE,
)


def is_ballot_context(chunks: list[dict[str, Any]]) -> bool:
    return any(c.get("doc_type") in ("ballot", "voter_guide") for c in chunks)


def has_persuasive_ballot_language(summary: str, chunks: list[dict[str, Any]]) -> bool:
    if not is_ballot_context(chunks):
        return False
    return bool(_PERSUASIVE.search(summary or ""))


def citations_are_grounded(summary: str, chunks: list[dict[str, Any]]) -> bool:
    """Require that a non-empty summary references at least one retrieved chunk.

    Lightweight check for step 4: summary must mention a title or include a
    [n] style citation index within range. Stricter claim-level checks later.
    """
    if not summary or not summary.strip():
        return False
    if not chunks:
        return False

    lower = summary.lower()
    for i, chunk in enumerate(chunks, start=1):
        title = (chunk.get("title") or "").lower()
        if title and title in lower:
            return True
        if re.search(rf"\[{i}\]", summary):
            return True
        # Short distinctive snippet from the chunk text
        snippet = (chunk.get("text") or "").strip()
        if len(snippet) >= 40 and snippet[:40].lower() in lower:
            return True

    return False


def validate_summary(
    summary: str | None,
    chunks: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    """Return (ok, error_reason). ok=False means do not show the summary."""
    if summary is None or not summary.strip():
        return False, "empty_summary"
    if has_persuasive_ballot_language(summary, chunks):
        return False, "ballot_persuasion"
    if not citations_are_grounded(summary, chunks):
        return False, "ungrounded_citations"
    return True, None
