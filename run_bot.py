"""Run only the Telegram bot (no FastAPI server)."""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from app.bot.telegram_bot import create_bot
from app.config import settings


async def main():
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    bot = create_bot()
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()
    print("Telegram bot is running. Press Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bot.updater.stop()
        await bot.stop()
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
