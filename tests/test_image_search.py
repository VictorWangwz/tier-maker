"""Tests for image search module."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.image_search import DuckDuckGoImageSearcher, fetch_images
from app.models import TierCategory, TierItem, TierListResult


@pytest.fixture
def sample_tier_data():
    return TierListResult(
        title="Test",
        categories=[
            TierCategory(
                tier_name="S",
                color="#FF7F7F",
                items=[
                    TierItem(name="Apple", search_keyword="Apple logo"),
                    TierItem(name="Samsung", search_keyword="Samsung logo"),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_fetch_images_success(sample_tier_data):
    mock_searcher = AsyncMock()
    mock_searcher.search.side_effect = ["url_apple", "url_samsung"]
    result = await fetch_images(sample_tier_data, searcher=mock_searcher)
    assert result.categories[0].items[0].image_url == "url_apple"
    assert result.categories[0].items[1].image_url == "url_samsung"


@pytest.mark.asyncio
async def test_fetch_images_failure_falls_back(sample_tier_data):
    mock_searcher = AsyncMock()
    mock_searcher.search.side_effect = ["url_apple", None]
    result = await fetch_images(sample_tier_data, searcher=mock_searcher)
    assert result.categories[0].items[0].image_url == "url_apple"
    assert result.categories[0].items[1].image_url is None
