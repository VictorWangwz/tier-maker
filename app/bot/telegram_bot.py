from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from app.config import settings
from app.image_search import TavilyImageSearcher, fetch_images
from app.llm import parse_tier_list
from app.renderer import render_tier_image

logger = logging.getLogger(__name__)


async def _handle_message(text: str) -> Path:
    """Run the full tier-list pipeline and return the generated image path."""
    tier_data = parse_tier_list(text)
    tier_data = await fetch_images(tier_data, searcher=TavilyImageSearcher(), context_text=text)
    image_path = await render_tier_image(tier_data)
    return image_path


async def start_cmd(update: Update, _context) -> None:
    await update.message.reply_text(
        "Send me a tier list description and I'll generate the image!\n\n"
        "Example:\n"
        "Apple and Samsung in S tier, Google in A tier, Xiaomi in B tier"
    )


async def generate_handler(update: Update, _context) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        return

    logger.info("Telegram request from %s: %s", update.effective_user, text[:80])

    await update.message.chat.send_action("upload_photo")

    try:
        image_path = await _handle_message(text)
        await update.message.reply_photo(
            photo=open(image_path, "rb"),
            caption=f"Here's your tier list!",
        )
    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
        await update.message.reply_text(
            "Sorry, something went wrong generating your tier list. Please try again."
        )


def create_bot():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to .env")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_handler))

    return app
