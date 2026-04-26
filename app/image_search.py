from __future__ import annotations

import asyncio
import logging
from typing import Optional, Protocol

from tavily import TavilyClient

from app.config import settings

logger = logging.getLogger(__name__)


class ImageSearcher(Protocol):
    async def search(self, keyword: str) -> Optional[str]: ...


class TavilyImageSearcher:
    """Fetches image URLs via Tavily search API."""

    async def search(self, keyword: str) -> Optional[str]:
        loop = asyncio.get_event_loop()
        try:
            client = TavilyClient(api_key=settings.tavily_api_key)
            response = await loop.run_in_executor(
                None,
                lambda: client.search(
                    query=keyword,
                    search_depth="basic",
                    include_images=True,
                    max_results=1,
                ),
            )
            images = response.get("images", [])
            if images:
                return images[0]
        except Exception as e:
            logger.warning("Tavily image search failed for '%s': %s", keyword, e)
        return None


async def fetch_images(
    tier_data: "TierListResult",
    searcher: Optional[ImageSearcher] = None,
) -> "TierListResult":
    """Populate image_url for every TierItem concurrently."""
    from app.models import TierListResult

    if searcher is None:
        searcher = TavilyImageSearcher()

    keywords = [
        item.search_keyword
        for cat in tier_data.categories
        for item in cat.items
    ]

    urls = await asyncio.gather(*(searcher.search(kw) for kw in keywords))

    idx = 0
    for cat in tier_data.categories:
        for item in cat.items:
            item.image_url = urls[idx]
            idx += 1

    return tier_data
