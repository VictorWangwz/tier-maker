from __future__ import annotations

import logging
from typing import Optional

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    input_text TEXT NOT NULL,
    email TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    image_path TEXT
);

CREATE TABLE IF NOT EXISTS tiers (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    tier_name TEXT NOT NULL,
    tier_order INTEGER NOT NULL,
    color TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    tier_id INTEGER NOT NULL REFERENCES tiers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    search_keyword TEXT NOT NULL,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS image_cache (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    context_text TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(keyword, context_text)
);
"""

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA)


async def create_job(input_text: str, email: str = "") -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO jobs (input_text, email) VALUES ($1, $2) RETURNING id",
            input_text, email,
        )
        return row["id"]


async def get_job(job_id: int) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
        return dict(row) if row else None


async def update_job_status(job_id: int, status: str, image_path: Optional[str] = None) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status == "done":
            await conn.execute(
                "UPDATE jobs SET status = $1, image_path = $2, completed_at = NOW() WHERE id = $3",
                status, image_path, job_id,
            )
        else:
            await conn.execute(
                "UPDATE jobs SET status = $1 WHERE id = $2",
                status, job_id,
            )


async def save_tiers(job_id: int, tier_data: "TierListResult") -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        for i, cat in enumerate(tier_data.categories):
            row = await conn.fetchrow(
                "INSERT INTO tiers (job_id, tier_name, tier_order, color) VALUES ($1, $2, $3, $4) RETURNING id",
                job_id, cat.tier_name, i, cat.color,
            )
            tier_id = row["id"]
            for item in cat.items:
                await conn.execute(
                    "INSERT INTO items (tier_id, name, search_keyword, image_url) VALUES ($1, $2, $3, $4)",
                    tier_id, item.name, item.search_keyword, item.image_url,
                )


async def get_job_tiers(job_id: int) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tiers WHERE job_id = $1 ORDER BY tier_order",
            job_id,
        )
        result = []
        for row in rows:
            tier = dict(row)
            items = await conn.fetch(
                "SELECT * FROM items WHERE tier_id = $1",
                tier["id"],
            )
            tier["items"] = [dict(i) for i in items]
            result.append(tier)
        return result


async def get_cached_image(keyword: str, context_text: str = "") -> Optional[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT image_url FROM image_cache WHERE keyword = $1 AND context_text = $2",
            keyword, context_text,
        )
        return row["image_url"] if row else None


async def cache_image(keyword: str, context_text: str, image_url: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO image_cache (keyword, context_text, image_url) VALUES ($1, $2, $3)
               ON CONFLICT (keyword, context_text) DO NOTHING""",
            keyword, context_text, image_url,
        )


async def list_recent_jobs(limit: int = 10) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, input_text, status, created_at FROM jobs WHERE status = 'done' ORDER BY completed_at DESC LIMIT $1",
            limit,
        )
        return [dict(r) for r in rows]
