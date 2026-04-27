# Auto Tier Maker

Generate beautiful tier-list images from natural language descriptions using AI. Automatically extracts tier rankings, searches for relevant images, and renders professional tier lists.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

## Features

- 🤖 **AI-Powered Parsing**: Uses LLM to structure natural language into tier lists
- 🔍 **Automatic Image Search**: Fetches relevant images via Tavily API
- 🎨 **Multiple Templates**: Adaptive layouts (compact/standard/massive) based on tier count
- 🗄️ **PostgreSQL Caching**: Persistent image cache to reduce API calls
- 🌐 **REST API**: Simple HTTP endpoints for generation
- 💬 **Telegram Bot**: Interactive bot interface
- 🐳 **Docker Support**: Full containerization with docker-compose
- ⚡ **Async Architecture**: Built on FastAPI with asyncio throughout

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Configuration](#configuration)
- [Usage](#usage)
  - [API Server](#api-server)
  - [Telegram Bot](#telegram-bot)
  - [Examples](#examples)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Architecture](#architecture)
- [License](#license)

## Requirements

- Python 3.11+
- PostgreSQL 16+ (or use Docker)
- Chromium (via Playwright)
- API Keys:
  - LLM endpoint (OpenAI-compatible API)
  - Tavily API key (for image search)
  - Telegram Bot Token (optional, for bot features)

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone and configure
git clone <your-repo-url>
cd auto-tier-maker
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker compose up

# 3. Access API at http://localhost:8000
curl http://localhost:8000/health
```

### Local Development

```bash
# 1. Setup (automated script)
chmod +x setup.sh
./setup.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run migrations and start server
python -m app.db  # Initialize database
uvicorn app.main:app --reload
```

## Installation

### Local Setup

#### Prerequisites

```bash
# Install Python 3.11+
python --version  # Should be 3.11 or higher

# Install PostgreSQL 16+ or use Docker for database only
docker compose up db -d
```

#### Install Dependencies

Using `pip`:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

Using `uv` (faster):
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### Install Playwright

```bash
playwright install chromium
```

#### Setup Directories

```bash
mkdir -p output cache
```

#### Initialize Database

```bash
# Start PostgreSQL (if using Docker)
docker compose up db -d

# Run schema initialization
python -c "import asyncio; from app.db import init_db; asyncio.run(init_db())"
```

### Docker Setup

```bash
# Build and start all services
docker compose up --build

# Or run in background
docker compose up -d

# View logs
docker compose logs -f app

# Stop services
docker compose down
```

## Configuration

Create a `.env` file in the project root:

```bash
# LLM Configuration (OpenAI-compatible API)
LLM_BASE_URL=http://localhost:8001/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini

# Or use Ollama locally
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=gemma3:12b
# LLM_API_KEY=not-needed

# Tavily API (for image search)
TAVILY_API_KEY=your-tavily-key-here

# Database
DATABASE_URL=postgresql://tiermaker:tiermaker@localhost:5432/tiermaker

# Server
HOST=0.0.0.0
PORT=8000

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Directories
OUTPUT_DIR=output
CACHE_DIR=cache
```

### Getting API Keys

1. **LLM API**: 
   - Use [OpenAI](https://platform.openai.com/api-keys)
   - Or run [Ollama](https://ollama.ai/) locally (free)
   - Or any OpenAI-compatible endpoint

2. **Tavily API**: 
   - Sign up at [Tavily](https://tavily.com/)
   - Free tier: 1,000 requests/month

3. **Telegram Bot** (optional):
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Use `/newbot` command to create a bot
   - Save the token provided

## Usage

### API Server

Start the server:

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If `TELEGRAM_BOT_TOKEN` is configured, the Telegram bot starts automatically.

### Telegram Bot

#### Standalone Bot (No HTTP Server)

```bash
python run_bot.py
```

#### Using the Bot

1. Find your bot on Telegram (use the username you created)
2. Start a chat: `/start`
3. Send a tier list description:
   ```
   Apple and Samsung in S tier, Google in A tier, Xiaomi in B tier
   ```
4. Receive the generated tier list image

### Examples

#### Example 1: Basic Tier List

**Input:**
```
Apple and Samsung in S tier, Google and OnePlus in A tier, Xiaomi in B tier
```

**API Request:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple and Samsung in S tier, Google and OnePlus in A tier, Xiaomi in B tier"
  }'
```

**Response:**
```json
{
  "image_url": "/images/tier_20260426_123456.png",
  "tier_data": {
    "title": "Smartphone Brands",
    "categories": [
      {
        "tier_name": "S",
        "color": "#FF7F7F",
        "items": [
          {
            "name": "Apple",
            "search_keyword": "Apple logo",
            "image_url": "https://..."
          },
          {
            "name": "Samsung",
            "search_keyword": "Samsung logo",
            "image_url": "https://..."
          }
        ]
      }
      // ... more tiers
    ]
  }
}
```

#### Example 2: Food Tier List

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Pizza and Sushi in S tier, Tacos and Burgers in A tier, Salad in C tier"
  }'
```

#### Example 3: Custom Tier Names

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Amazing tier: Tesla, Great tier: Toyota Honda, Good tier: Ford"
  }'
```

## API Documentation

### Endpoints

#### `GET /health`

Health check endpoint.

**Response:**
```json
{"status": "ok"}
```

#### `POST /generate`

Generate a tier list image from text.

**Request Body:**
```json
{
  "text": "Your tier list description here"
}
```

**Response:**
```json
{
  "image_url": "/images/filename.png",
  "tier_data": {
    "title": "Generated title",
    "categories": [...]
  }
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid input (empty text)
- `500`: Generation error

#### `GET /images/{filename}`

Retrieve a generated tier list image.

**Response:** PNG image file

**Status Codes:**
- `200`: Success
- `404`: Image not found

### Interactive API Docs

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
auto-tier-maker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, lifespan
│   ├── config.py            # Settings (pydantic-settings)
│   ├── models.py            # Pydantic schemas
│   ├── llm.py              # LLM integration (LangChain)
│   ├── image_search.py     # Tavily image search
│   ├── templates.py        # Template selector
│   ├── renderer.py         # Playwright HTML→PNG renderer
│   ├── db.py               # PostgreSQL connection & queries
│   ├── bot/
│   │   ├── __init__.py
│   │   └── telegram_bot.py # Telegram bot handler
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html       # Base layout
│       ├── compact.html    # 1-3 tiers
│       ├── standard.html   # 4-6 tiers
│       └── massive.html    # 7+ tiers
├── tests/
│   ├── test_api.py
│   ├── test_llm.py
│   ├── test_image_search.py
│   └── test_models.py
├── output/                  # Generated images (gitignored)
├── cache/                   # Local cache files (gitignored)
├── static/                  # Static assets (if any)
├── .env                     # Environment variables (gitignored)
├── .env.example            # Example configuration
├── docker-compose.yml      # Docker services
├── Dockerfile              # App container
├── pyproject.toml          # Python project metadata
├── requirements.txt        # Legacy requirements (deprecated)
├── run_bot.py              # Standalone bot runner
├── setup.sh                # Linux/Mac setup script
├── setup.bat               # Windows setup script
├── CLAUDE.md               # Development notes
└── README.md               # This file
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_llm.py -v

# Run specific test
pytest tests/test_llm.py::test_parse_tier_list -v
```

### VS Code Debugging

The project includes pre-configured debug configurations in `.vscode/launch.json`:

- **API Server (uvicorn)**: Debug the FastAPI server with auto-reload
- **Telegram Bot Only**: Debug just the Telegram bot
- **API Server + Telegram Bot**: Debug both together
- **Pytest: All Tests**: Debug all tests
- **Pytest: Current File**: Debug the currently open test file
- **Python: Current File**: Debug any Python file

### Code Quality

```bash
# Format code
black app/ tests/

# Type checking
mypy app/

# Linting
ruff check app/ tests/
```

### Database Management

```bash
# Connect to database
docker compose exec db psql -U tiermaker -d tiermaker

# Reset database
docker compose down -v
docker compose up db -d
python -c "import asyncio; from app.db import init_db; asyncio.run(init_db())"
```

## Architecture

### Component Overview

```
┌─────────────┐
│   User      │
│  Input      │
└──────┬──────┘
       │
       ├──► REST API ──────────┐
       │                       │
       └──► Telegram Bot ──────┤
                               │
                               ▼
                      ┌────────────────┐
                      │  LLM Parser    │
                      │  (LangChain)   │
                      └────────┬───────┘
                               │
                               ▼
                      ┌────────────────┐
                      │ Image Searcher │◄──► PostgreSQL
                      │   (Tavily)     │     (Cache)
                      └────────┬───────┘
                               │
                               ▼
                      ┌────────────────┐
                      │   Renderer     │
                      │  (Playwright)  │
                      └────────┬───────┘
                               │
                               ▼
                      ┌────────────────┐
                      │  PNG Image     │
                      └────────────────┘
```

### Design Principles

- **Pluggable Components**: All major components (LLM, image search, renderer) follow protocols/interfaces
- **Async-First**: Built on asyncio for efficient I/O operations
- **Database Caching**: Reduces external API calls and costs
- **Template Flexibility**: Jinja2 templates with inheritance for easy customization
- **Configuration**: All settings via environment variables (12-factor app)

### Adding New Features

#### Add a New Image Search Provider

1. Implement the `ImageSearcher` protocol in [app/image_search.py](app/image_search.py)
2. Update configuration to select provider
3. Example: Google Images, Bing Images, etc.

#### Add a New Chat Platform

1. Create `app/bot/whatsapp_bot.py` (or other platform)
2. Implement the same pipeline as Telegram bot
3. Register in [app/main.py](app/main.py) lifespan

#### Customize Templates

1. Edit existing templates in `app/templates/`
2. Or create new ones and update `app/templates.py`
3. Templates use Jinja2 syntax

## Testing

### Test Coverage

Run tests with coverage report:

```bash
pytest --cov=app --cov-report=html tests/
# Open htmlcov/index.html in browser
```

### Integration Tests

```bash
# Requires running database
docker compose up db -d
pytest tests/ -v -k integration
```

### Manual Testing

```bash
# Test the full pipeline
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Test in S tier"}' \
  | jq .

# Check generated image
open output/*.png  # Mac
xdg-open output/*.png  # Linux
start output\*.png  # Windows
```

## Troubleshooting

### Common Issues

**Database connection error**
```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
docker compose restart db
```

**Playwright/Chromium issues**
```bash
# Reinstall Chromium
playwright install chromium --force
```

**LLM returns invalid JSON**
```bash
# Check your LLM configuration
# Some models need specific prompts or settings
# Try adjusting temperature in app/llm.py
```

**Images not loading**
```bash
# Check Tavily API key
echo $TAVILY_API_KEY

# Check database cache
docker compose exec db psql -U tiermaker -d tiermaker
SELECT COUNT(*) FROM image_cache;
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Image search by [Tavily](https://tavily.com/)
- LLM integration via [LangChain](https://langchain.com/)
- Rendering by [Playwright](https://playwright.dev/)
- Bot framework: [python-telegram-bot](https://python-telegram-bot.org/)

---

**Need help?** Open an issue on GitHub or check the [CLAUDE.md](CLAUDE.md) development notes.