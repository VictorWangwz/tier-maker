from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.models import TierListResult
from app.templates import TEMPLATES_DIR

logger = logging.getLogger(__name__)

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


async def render_tier_image(
    tier_data: TierListResult,
    template_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    if template_path is None:
        from app.templates import select_template

        template_path = select_template(len(tier_data.categories))

    if output_dir is None:
        output_dir = settings.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    template = _jinja_env.get_template(template_path.name)
    html_content = template.render(tier=tier_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in tier_data.title)[:40]
    output_path = output_dir / f"{safe_title}_{timestamp}.png"

    await asyncio.to_thread(_screenshot_sync, html_content, output_path)
    return output_path


def _screenshot_sync(html: str, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=str(output_path), full_page=True)
        browser.close()
        logger.info("Saved tier list image to %s", output_path)
