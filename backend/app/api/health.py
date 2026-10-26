from fastapi import APIRouter

from app.db import get_connection
from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    db_ok = False
    redis_ok = False
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_ok = get_redis().ping() is True
    except Exception:
        redis_ok = False

    status = "ok" if db_ok and redis_ok else "degraded"
    return {"status": status, "db": db_ok, "redis": redis_ok}
