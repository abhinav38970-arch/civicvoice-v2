"""Password hashing and signed session cookies."""

from __future__ import annotations

import uuid
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings
from app.redis_client import get_redis

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.session_secret, salt="civicvoice-session")


def create_session_token(user_id: uuid.UUID) -> str:
    return _serializer().dumps({"uid": str(user_id)})


def read_session_token(token: str) -> uuid.UUID | None:
    settings = get_settings()
    try:
        data: dict[str, Any] = _serializer().loads(
            token, max_age=settings.session_max_age_seconds
        )
        return uuid.UUID(data["uid"])
    except (BadSignature, SignatureExpired, KeyError, ValueError):
        return None


def _fail_key(email: str) -> str:
    return f"login_fail:{email.lower()}"


def _lock_key(email: str) -> str:
    return f"login_lock:{email.lower()}"


def is_login_locked(email: str) -> bool:
    return bool(get_redis().exists(_lock_key(email)))


def record_login_failure(email: str) -> int:
    """Increment failure count; lock after max failures. Returns current count."""
    settings = get_settings()
    r = get_redis()
    key = _fail_key(email)
    count = int(r.incr(key))
    if count == 1:
        r.expire(key, settings.login_lockout_seconds)
    if count >= settings.login_max_failures:
        r.setex(_lock_key(email), settings.login_lockout_seconds, "1")
        r.delete(key)
    return count


def clear_login_failures(email: str) -> None:
    r = get_redis()
    r.delete(_fail_key(email), _lock_key(email))
