from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = "not-needed"
    llm_model: str = "gemma3:12b"

    host: str = "0.0.0.0"
    port: int = 8000

    output_dir: Path = Path("output")
    cache_dir: Path = Path("cache")

    tavily_api_key: str = ""

    telegram_bot_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
