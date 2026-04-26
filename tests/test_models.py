"""Tests for Pydantic models and data validation."""
import pytest
from pydantic import ValidationError

from app.models import TierCategory, TierItem, TierListResult, GenerateRequest


def test_tier_item_defaults():
    item = TierItem(name="Apple", search_keyword="Apple logo")
    assert item.image_url is None


def test_tier_item_with_url():
    item = TierItem(name="Apple", search_keyword="Apple logo", image_url="https://example.com/apple.png")
    assert item.image_url == "https://example.com/apple.png"


def test_tier_category():
    items = [
        TierItem(name="Apple", search_keyword="Apple logo"),
        TierItem(name="Samsung", search_keyword="Samsung logo"),
    ]
    cat = TierCategory(tier_name="S", color="#FF7F7F", items=items)
    assert len(cat.items) == 2
    assert cat.tier_name == "S"


def test_tier_list_result():
    data = TierListResult(
        title="Phone Brands",
        categories=[
            TierCategory(
                tier_name="S",
                color="#FF7F7F",
                items=[TierItem(name="Apple", search_keyword="Apple logo")],
            ),
            TierCategory(
                tier_name="A",
                color="#FFBF7F",
                items=[TierItem(name="Google", search_keyword="Google Pixel logo")],
            ),
        ],
    )
    assert len(data.categories) == 2
    assert data.categories[0].items[0].name == "Apple"


def test_generate_request_empty():
    with pytest.raises(ValidationError):
        GenerateRequest(text="")


def test_generate_request_valid():
    req = GenerateRequest(text="Apple in S, Samsung in A")
    assert req.text == "Apple in S, Samsung in A"
