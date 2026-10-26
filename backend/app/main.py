from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_routes, feed, health
from app.db import close_pool, init_pool
from app.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_pool()
    get_redis().ping()
    yield
    close_pool()
    close_redis()


app = FastAPI(
    title="CivicVoice API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(feed.router)
