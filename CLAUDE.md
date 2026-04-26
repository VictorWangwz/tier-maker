# Auto Tier Maker

Generates tier-list images from natural language input using LLM structuring, image search, and headless browser rendering. Accessible via REST API or Telegram bot.

## Quick Start

```bash
uv venv && source .venv/bin/activate   # or: python -m venv .venv
uv pip install -r requirements.txt      # or: pip install -r requirements.txt
playwright install chromium
cp .env.example .env                    # edit LLM_BASE_URL / LLM_MODEL / TELEGRAM_BOT_TOKEN
```

### Run API server (with optional Telegram bot)

```bash
uvicorn app.main:app --reload
```

If `TELEGRAM_BOT_TOKEN` is set in `.env`, the Telegram bot starts automatically alongside the API.

### Run Telegram bot only

```bash
python run_bot.py
```

## API

| Endpoint | Method | Body | Response |
|---|---|---|---|
| `/health` | GET | — | `{"status":"ok"}` |
| `/generate` | POST | `{"text":"..."}` | `{"image_url":"...", "tier_data":{...}}` |
| `/image/{filename}` | GET | — | PNG file |

### Example

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple and Samsung in S tier, Google in A tier, Xiaomi in B tier"}'
```

## Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram to create a bot and get a token.
2. Set `TELEGRAM_BOT_TOKEN` in `.env`.
3. Start the server or `python run_bot.py`.
4. Send a message like "Apple in S tier, Samsung in A tier" to your bot — it replies with the generated image.

## Project Structure

```
app/
  config.py          — pydantic-settings, reads .env
  models.py          — Pydantic schemas (TierItem, TierCategory, TierListResult)
  llm.py             — OpenAI SDK client → structured tier JSON, regex fallback
  image_search.py    — DuckDuckGo image fetch (async), pluggable via Protocol
  templates.py       — rule-based template selector (compact/standard/massive)
  renderer.py        — Jinja2 + Playwright → PNG
  templates/         — HTML/CSS tier list layouts (Jinja2 inheritance)
  bot/
    telegram_bot.py  — Telegram bot handler (receives text, sends back image)
  main.py            — FastAPI app, routes, lifespan (starts bot if token is set)
run_bot.py           — Standalone Telegram bot runner (no HTTP server)
tests/               — pytest unit + integration tests
output/              — generated PNGs (gitignored)
```

## Architecture Notes

- **LLM**: Uses OpenAI SDK pointed at configurable `base_url`. Swap providers by changing `LLM_BASE_URL` and `LLM_MODEL` in `.env`.
- **Image Search**: `ImageSearcher` protocol in `image_search.py`. Add new providers (Google, Bing) by implementing the protocol.
- **Templates**: Jinja2 inheritance from `base.html`. Add new layouts by creating a child template and updating `templates.py`.
- **Renderer**: Playwright headless Chromium. Swap for other renderers by editing `renderer.py`.
- **Bots**: `app/bot/` module. Each platform is a separate file. Add WhatsApp/WeChat by creating a new file implementing the same pipeline. Currently Telegram-only.
- All config flows through `app/config.py` via pydantic-settings.
