"""Robust display-text translation.

Lookup order:
  1. Redis
  2. Postgres text_translations
  3. Built-in glossary (demo / known civic phrases)
  4. Live providers (MyMemory → Google) with retries + circuit breaker

Successful live results are written to Redis and Postgres so the dashboard
stays localized after free-API quotas are exhausted.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
from typing import Callable

from app.db import get_connection
from app.redis_client import get_redis

logger = logging.getLogger(__name__)

# MyMemory requires locale-style codes (plain "en" / "hi" are rejected).
_MYMEMORY = {
    "hi": ("en-GB", "hi-IN"),
    "es": ("en-GB", "es-ES"),
    "zh": ("en-GB", "zh-CN"),
    "pa": ("en-GB", "pa-IN"),
    "fa": ("en-GB", "fa-IR"),
    "ar": ("en-GB", "ar-SA"),
    "ko": ("en-GB", "ko-KR"),
    "vi": ("en-GB", "vi-VN"),
    "pt": ("en-GB", "pt-PT"),
    "tl": ("en-GB", "tl-PH"),
    "ur": ("en-GB", "ur-PK"),
}

_GOOGLE = {
    "hi": "hi",
    "es": "es",
    "zh": "zh-CN",
    "pa": "pa",
    "fa": "fa",
    "ar": "ar",
    "ko": "ko",
    "vi": "vi",
    "pt": "pt",
    "tl": "tl",
    "ur": "ur",
}

# Script / alphabet hints — reject responses that are still English.
_SCRIPT_OK: dict[str, re.Pattern[str] | None] = {
    "hi": re.compile(r"[\u0900-\u097F]"),
    "pa": re.compile(r"[\u0A00-\u0A7F]"),
    "zh": re.compile(r"[\u4e00-\u9fff]"),
    "ko": re.compile(r"[\uac00-\ud7af]"),
    "ar": re.compile(r"[\u0600-\u06FF]"),
    "fa": re.compile(r"[\u0600-\u06FF]"),
    "ur": re.compile(r"[\u0600-\u06FF]"),
    "es": None,
    "pt": None,
    "vi": None,
    "tl": None,
}

# Curated fallbacks for high-traffic civic phrases (used when live APIs are down).
_GLOSSARY: dict[str, dict[str, str]] = {
    "hi": {
        "Alameda County Registrar of Voters": "अलामेडा काउंटी रजिस्ट्रार ऑफ़ वोटर्स",
        "California Vote by Mail information": "मेल द्वारा कैलिफ़ोर्निया वोट की जानकारी",
        "California Voter Information Guides": "कैलिफ़ोर्निया मतदाता सूचना मार्गदर्शिकाएँ",
        "California Elections and Voter Information": "कैलिफ़ोर्निया चुनाव और मतदाता जानकारी",
        "California Secretary of State — Voter Information Guides": "कैलिफ़ोर्निया राज्य सचिव — मतदाता सूचना मार्गदर्शिकाएँ",
        "California Secretary of State — Elections": "कैलिफ़ोर्निया राज्य सचिव — चुनाव",
        "Alameda County — Vote by Mail & ballot status": "अलामेडा काउंटी — मेल द्वारा मतदान और मतपत्र स्थिति",
        "City of Fremont (sample)": "फ़्रीमॉन्ट शहर (नमूना)",
        "Official page": "आधिकारिक पेज",
        "News": "समाचार",
        "Council": "काउंसिल",
        "Ballot": "बैलट",
        "Voter guide": "मतदाता गाइड",
    },
    "es": {
        "Alameda County Registrar of Voters": "Registrador de votantes del condado de Alameda",
        "California Vote by Mail information": "Información de voto por correo de California",
        "California Voter Information Guides": "Guías de información para votantes de California",
        "California Elections and Voter Information": "Elecciones e información para votantes de California",
    },
    "zh": {
        "Alameda County Registrar of Voters": "阿拉米达县选民登记处",
        "California Vote by Mail information": "加州邮寄投票信息",
        "California Voter Information Guides": "加州选民信息指南",
        "California Elections and Voter Information": "加州选举与选民信息",
    },
}

_CACHE_TTL = 60 * 60 * 24 * 90
_MYMEMORY_MAX = 450
_GOOGLE_MAX = 4500
_MAX_RETRIES = 2
_CIRCUIT_SECONDS = 30 * 60

_lock = threading.Lock()
_last_call = 0.0
_inflight: dict[str, threading.Event] = {}
_circuit_until: dict[str, float] = {}


def _source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_key(lang: str, text: str) -> str:
    return f"tr:{lang}:{_source_hash(text)[:32]}"


def _circuit_open(provider: str) -> bool:
    return time.time() < _circuit_until.get(provider, 0.0)


def _trip_circuit(provider: str, seconds: float = _CIRCUIT_SECONDS) -> None:
    until = time.time() + seconds
    _circuit_until[provider] = max(_circuit_until.get(provider, 0.0), until)
    logger.warning("translate circuit open provider=%s for %.0fs", provider, seconds)


def _throttle(min_interval: float = 0.4) -> None:
    global _last_call
    with _lock:
        wait = min_interval - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()


def _looks_translated(source: str, out: str, lang: str) -> bool:
    if not out or not out.strip():
        return False
    cleaned = out.strip()
    if cleaned == source.strip():
        return False
    upper = cleaned.upper()
    if upper.startswith("MYMEMORY") or "QUERY LENGTH LIMIT" in upper or "YOU USED ALL" in upper:
        return False
    hint = _SCRIPT_OK.get(lang)
    if hint is not None and not hint.search(cleaned):
        return False
    return True


def _chunks(text: str, max_len: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    buf = ""
    for piece in re.split(r"(?<=[.!?。！？\n])\s+", text):
        if not piece:
            continue
        if len(buf) + len(piece) + 1 <= max_len:
            buf = f"{buf} {piece}".strip() if buf else piece
        else:
            if buf:
                parts.append(buf)
            if len(piece) <= max_len:
                buf = piece
            else:
                for i in range(0, len(piece), max_len):
                    parts.append(piece[i : i + max_len])
                buf = ""
    if buf:
        parts.append(buf)
    return parts or [text[:max_len]]


def _redis_get(key: str) -> str | None:
    try:
        return get_redis().get(key)
    except Exception as exc:
        logger.debug("redis get failed: %s", exc)
        return None


def _redis_set(key: str, value: str) -> None:
    try:
        get_redis().setex(key, _CACHE_TTL, value)
    except Exception as exc:
        logger.debug("redis set failed: %s", exc)


def _db_get(source_hash: str, lang: str) -> str | None:
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT translated_text
                FROM text_translations
                WHERE source_hash = %s AND language = %s
                """,
                (source_hash, lang),
            ).fetchone()
            return row["translated_text"] if row else None
    except Exception as exc:
        logger.debug("db get translation failed: %s", exc)
        return None


def _db_set(source_hash: str, lang: str, source: str, translated: str, provider: str) -> None:
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO text_translations (
                    source_hash, language, source_text, translated_text, provider, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (source_hash, language) DO UPDATE
                  SET translated_text = EXCLUDED.translated_text,
                      provider = EXCLUDED.provider,
                      updated_at = now()
                """,
                (source_hash, lang, source, translated, provider),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("db set translation failed: %s", exc)


def _store(lang: str, source: str, translated: str, provider: str) -> str:
    _redis_set(_cache_key(lang, source), translated)
    _db_set(_source_hash(source), lang, source, translated, provider)
    return translated


def store_translation(lang: str, source: str, translated: str, provider: str = "seed") -> str:
    """Public helper for seed/catalog warm paths."""
    if not source or not translated:
        return source
    return _store(lang, source, translated, provider)


def reset_circuits() -> None:
    """Clear provider circuit breakers (e.g. after seeding durable cache)."""
    _circuit_until.clear()


def _glossary_get(source: str, lang: str) -> str | None:
    table = _GLOSSARY.get(lang) or {}
    cleaned = source.strip()
    hit = table.get(cleaned)
    if hit and _looks_translated(cleaned, hit, lang):
        return hit
    # Case-insensitive exact match
    lower = cleaned.lower()
    for k, v in table.items():
        if k.lower() == lower and _looks_translated(cleaned, v, lang):
            return v
    # Prefix match: catalog list uses left(220) of longer seeded bodies.
    if len(cleaned) >= 40:
        best_key = None
        for k, v in table.items():
            if len(k) <= len(cleaned):
                continue
            if k.startswith(cleaned) or k.lower().startswith(lower):
                if best_key is None or len(k) < len(best_key):
                    best_key = k
        if best_key:
            full = table[best_key]
            # Approximate display slice: keep similar character budget.
            ratio = len(cleaned) / max(len(best_key), 1)
            cut = max(40, int(len(full) * ratio) + 8)
            sliced = full[:cut].rstrip()
            if _looks_translated(cleaned, sliced, lang):
                return sliced
    return None


def _is_rate_limit(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    return (
        "toomanyrequests" in name
        or "too many requests" in msg
        or "429" in msg
        or "rate" in msg and "limit" in msg
    )


def _try_mymemory(text: str, lang: str) -> str | None:
    if _circuit_open("mymemory"):
        return None
    pair = _MYMEMORY.get(lang)
    if not pair:
        return None
    try:
        from deep_translator import MyMemoryTranslator
        from deep_translator.exceptions import TooManyRequests
    except ImportError:
        return None

    pieces: list[str] = []
    for part in _chunks(text, _MYMEMORY_MAX):
        out: str | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                _throttle(0.35 + attempt * 0.2)
                out = MyMemoryTranslator(source=pair[0], target=pair[1]).translate(part)
                if out and _looks_translated(part, out, lang):
                    break
                # Quota warning embedded in body
                if out and "YOU USED ALL" in out.upper():
                    _trip_circuit("mymemory")
                    return None
                out = None
            except TooManyRequests as exc:
                _trip_circuit("mymemory")
                logger.debug("MyMemory rate-limited: %s", exc)
                return None
            except Exception as exc:
                if _is_rate_limit(exc):
                    _trip_circuit("mymemory")
                    return None
                time.sleep(0.4 * (attempt + 1))
        if not out:
            return None
        pieces.append(out.strip())
    joined = " ".join(pieces).strip()
    return joined if _looks_translated(text, joined, lang) else None


def _try_google(text: str, lang: str) -> str | None:
    if _circuit_open("google"):
        return None
    dest = _GOOGLE.get(lang)
    if not dest:
        return None
    try:
        from deep_translator import GoogleTranslator
        from deep_translator.exceptions import TooManyRequests
    except ImportError:
        return None

    pieces: list[str] = []
    for part in _chunks(text, _GOOGLE_MAX):
        out: str | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                _throttle(0.7 + attempt * 0.3)
                out = GoogleTranslator(source="en", target=dest).translate(part)
                if out and _looks_translated(part, out, lang):
                    break
                out = None
            except TooManyRequests as exc:
                _trip_circuit("google")
                logger.warning("Google rate-limited: %s", exc)
                return None
            except Exception as exc:
                if _is_rate_limit(exc):
                    _trip_circuit("google")
                    return None
                time.sleep(0.8 * (attempt + 1))
        if not out:
            return None
        pieces.append(out.strip())
    joined = " ".join(pieces).strip()
    return joined if _looks_translated(text, joined, lang) else None


_PROVIDERS: list[tuple[str, Callable[[str, str], str | None]]] = [
    ("mymemory", _try_mymemory),
    ("google", _try_google),
]


def translate_text(
    text: str,
    target_lang: str,
    *,
    allow_live: bool = True,
) -> str:
    """Translate `text` into `target_lang`. Returns original on hard failure."""
    if not text or not text.strip():
        return text
    lang = (target_lang or "en").lower().strip()
    if lang == "en" or (lang not in _MYMEMORY and lang not in _GOOGLE):
        return text

    source = text
    key = _cache_key(lang, source)
    digest = _source_hash(source)

    cached = _redis_get(key)
    if cached and _looks_translated(source, cached, lang):
        # Keep Postgres warm even if only Redis had it.
        if _db_get(digest, lang) is None:
            _db_set(digest, lang, source, cached, "redis-backfill")
        return cached

    db_hit = _db_get(digest, lang)
    if db_hit and _looks_translated(source, db_hit, lang):
        _redis_set(key, db_hit)
        return db_hit

    gloss = _glossary_get(source, lang)
    if gloss:
        return _store(lang, source, gloss, "glossary")

    if not allow_live:
        return source

    with _lock:
        event = _inflight.get(key)
        mine = event is None
        if mine:
            event = threading.Event()
            _inflight[key] = event
    if not mine:
        event.wait(timeout=20)
        again = _redis_get(key) or _db_get(digest, lang)
        return again if again and _looks_translated(source, again, lang) else source

    try:
        for name, fn in _PROVIDERS:
            out = fn(source, lang)
            if out:
                return _store(lang, source, out, name)
        logger.info(
            "translate miss lang=%s hash=%s circuits=%s",
            lang,
            digest[:12],
            {k: round(v - time.time()) for k, v in _circuit_until.items() if v > time.time()},
        )
        return source
    finally:
        with _lock:
            ev = _inflight.pop(key, None)
            if ev:
                ev.set()


def persist_chunk_translation(
    chunk_id: str,
    language: str,
    translated_text: str,
    provider: str = "live",
) -> None:
    """Write a chunk translation so document pages stay warm."""
    if not translated_text or not translated_text.strip():
        return
    lang = language.lower().strip()
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO translations (
                    chunk_id, language, translated_text, provider, verified
                )
                VALUES (%s, %s, %s, %s, false)
                ON CONFLICT (chunk_id, language) DO UPDATE
                  SET translated_text = EXCLUDED.translated_text,
                      provider = EXCLUDED.provider
                """,
                (chunk_id, lang, translated_text, provider),
            )
            conn.commit()
    except Exception as exc:
        logger.warning("persist chunk translation failed: %s", exc)
