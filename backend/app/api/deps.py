from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import Cookie, Depends, HTTPException, status

from app.auth import read_session_token
from app.db import get_connection


def current_user_from_cookie(
    civicvoice_session: Annotated[str | None, Cookie()] = None,
) -> uuid.UUID:
    if not civicvoice_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in",
        )
    user_id = read_session_token(civicvoice_session)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return user_id


def load_user(user_id: uuid.UUID) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, email, preferred_language, city, interests, profession, created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return row


def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(current_user_from_cookie)],
) -> dict[str, Any]:
    return load_user(user_id)
