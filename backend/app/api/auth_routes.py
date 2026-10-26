from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import get_current_user
from app.auth import (
    clear_login_failures,
    create_session_token,
    hash_password,
    is_login_locked,
    record_login_failure,
    verify_password,
)
from app.config import SUPPORTED_LANGUAGES, get_settings
from app.db import get_connection

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    preferred_language: str = "en"
    interests: list[str] = Field(default_factory=list)
    profession: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class ProfileUpdateRequest(BaseModel):
    interests: list[str] | None = None
    profession: str | None = None
    city: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = None


def _user_public(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "preferred_language": row["preferred_language"],
        "city": row["city"],
        "interests": list(row["interests"] or []),
        "profession": row["profession"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _set_session_cookie(response: Response, user_id) -> None:
    settings = get_settings()
    token = create_session_token(user_id)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, response: Response) -> dict:
    lang = body.preferred_language.lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Use one of: {', '.join(SUPPORTED_LANGUAGES)}",
        )

    password_hash = hash_password(body.password)
    interests = [i.strip() for i in body.interests if i and i.strip()]

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                INSERT INTO users (
                    email, password_hash, preferred_language, city, interests, profession
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, email, preferred_language, city, interests, profession, created_at
                """,
                (
                    body.email.lower().strip(),
                    password_hash,
                    lang,
                    body.city.strip(),
                    interests,
                    body.profession.strip() if body.profession else None,
                ),
            ).fetchone()
            conn.commit()
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    _set_session_cookie(response, row["id"])
    return {"user": _user_public(row)}


@router.post("/login")
def login(body: LoginRequest, response: Response) -> dict:
    email = body.email.lower().strip()

    if is_login_locked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed logins. Try again in 10 minutes.",
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, email, password_hash, preferred_language, city, interests, profession, created_at
            FROM users
            WHERE email = %s
            """,
            (email,),
        ).fetchone()

    if row is None or not verify_password(row["password_hash"], body.password):
        count = record_login_failure(email)
        settings = get_settings()
        remaining = max(0, settings.login_max_failures - count)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid email or password. {remaining} attempts left before lockout.",
        )

    clear_login_failures(email)
    _set_session_cookie(response, row["id"])
    return {"user": _user_public(row)}


@router.post("/logout")
def logout(response: Response) -> dict:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )
    return {"ok": True}


@router.get("/me")
def me(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    return {"user": _user_public(user)}


@router.post("/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    # Partial update: omitted fields keep current values.
    if body.interests is None:
        interests = list(user["interests"] or [])
    else:
        interests = [i.strip() for i in body.interests if i and i.strip()]

    city = (
        body.city.strip()
        if body.city is not None and body.city.strip()
        else (user["city"] or "Fremont")
    )
    if body.profession is None:
        profession = user.get("profession")
    else:
        profession = body.profession.strip() or None

    lang = (
        body.preferred_language or user["preferred_language"] or "en"
    ).lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Use one of: {', '.join(SUPPORTED_LANGUAGES)}",
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            UPDATE users
            SET interests = %s,
                profession = %s,
                city = %s,
                preferred_language = %s
            WHERE id = %s
            RETURNING id, email, preferred_language, city, interests, profession, created_at
            """,
            (interests, profession, city, lang, user["id"]),
        ).fetchone()
        conn.commit()

    return {"ok": True, "user": _user_public(row)}
