from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import (
    create_job,
    get_job,
    get_job_tiers,
    init_db,
    list_recent_jobs,
    save_tiers,
    update_job_status,
)
from app.image_search import TavilyImageSearcher, fetch_images
from app.llm import parse_tier_list
from app.models import GenerateRequest, GenerateResponse
from app.renderer import render_tier_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_telegram_task: asyncio.Task | None = None


def _start_telegram():
    if not settings.telegram_bot_token:
        logger.info("TELEGRAM_BOT_TOKEN not set, skipping Telegram bot")
        return None

    from app.bot.telegram_bot import create_bot

    bot = create_bot()

    async def _run():
        await bot.initialize()
        await bot.start()
        await bot.updater.start_polling()
        logger.info("Telegram bot started")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await bot.updater.stop()
            await bot.stop()
            await bot.shutdown()

    return asyncio.create_task(_run())


async def _stop_telegram():
    global _telegram_task
    if _telegram_task:
        _telegram_task.cancel()
        try:
            await _telegram_task
        except asyncio.CancelledError:
            pass
        _telegram_task = None
        logger.info("Telegram bot stopped")


async def _process_job(job_id: int, input_text: str) -> None:
    try:
        await update_job_status(job_id, "running")
        tier_data = parse_tier_list(input_text)
        tier_data = await fetch_images(
            tier_data, searcher=TavilyImageSearcher(), context_text=input_text
        )
        await save_tiers(job_id, tier_data)
        image_path = await render_tier_image(tier_data)
        await update_job_status(job_id, "done", image_path=str(image_path))
    except Exception as e:
        logger.error("Job %d failed: %s", job_id, e, exc_info=True)
        await update_job_status(job_id, "failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    logger.info("Output directory: %s", settings.output_dir.resolve())
    global _telegram_task
    _telegram_task = _start_telegram()
    yield
    await _stop_telegram()


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Auto Tier Maker", lifespan=lifespan)
app.mount("/images", StaticFiles(directory=str(settings.output_dir)), name="images")


@app.get("/", response_class=HTMLResponse)
async def index():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    tier_data = parse_tier_list(req.text)
    tier_data = await fetch_images(tier_data, searcher=TavilyImageSearcher(), context_text=req.text)

    image_path = await render_tier_image(tier_data)
    image_url = f"/images/{image_path.name}"

    return GenerateResponse(image_url=image_url, tier_data=tier_data)


# --- Job API ---


@app.post("/jobs")
async def create_job_endpoint(req: GenerateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    job_id = await create_job(req.text.strip())
    asyncio.create_task(_process_job(job_id, req.text.strip()))
    return {"id": job_id, "status": "pending"}


@app.get("/jobs/{job_id}")
async def get_job_endpoint(job_id: int):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result = {
        "id": job["id"],
        "status": job["status"],
        "input_text": job["input_text"],
        "created_at": job["created_at"].isoformat() if job["created_at"] else None,
        "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
    }
    if job["status"] == "done":
        tiers = await get_job_tiers(job_id)
        result["tiers"] = [
            {
                "tier_name": t["tier_name"],
                "color": t["color"],
                "items": [
                    {"name": i["name"], "image_url": i["image_url"]}
                    for i in t["items"]
                ],
            }
            for t in tiers
        ]
        result["image_url"] = f"/images/{Path(job['image_path']).name}" if job["image_path"] else None
    return result


@app.get("/jobs")
async def list_jobs_endpoint():
    return await list_recent_jobs()


@app.get("/image/{filename}")
async def get_image(filename: str):
    path = settings.output_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")
