from __future__ import annotations

import asyncio
import hashlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", settings.output_dir.resolve())
    global _telegram_task
    _telegram_task = _start_telegram()
    yield
    await _stop_telegram()


app = FastAPI(title="Auto Tier Maker", lifespan=lifespan)
app.mount("/images", StaticFiles(directory=str(settings.output_dir)), name="images")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    cache_key = hashlib.sha256(req.text.strip().lower().encode()).hexdigest()
    cache_file = settings.cache_dir / f"{cache_key}.json"

    if cache_file.exists():
        logger.info("Cache hit for: %s", req.text[:80])
        tier_data = GenerateResponse.model_validate_json(cache_file.read_text(encoding="utf-8")).tier_data
    else:
        logger.info("Parsing tier list from: %s", req.text[:80])
        tier_data = parse_tier_list(req.text)
        tier_data = await fetch_images(tier_data, searcher=TavilyImageSearcher())
        cache_file.write_text(
            GenerateResponse(image_url="", tier_data=tier_data).model_dump_json(),
            encoding="utf-8",
        )

    image_path = await render_tier_image(tier_data)
    image_url = f"/images/{image_path.name}"

    return GenerateResponse(image_url=image_url, tier_data=tier_data)


@app.get("/image/{filename}")
async def get_image(filename: str):
    path = settings.output_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")
