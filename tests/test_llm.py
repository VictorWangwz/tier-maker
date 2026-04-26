"""Tests for LLM parsing logic (unit tests without actual LLM calls)."""
import json

from app.llm import _assign_colors, _parse_llm_output, _regex_fallback, TIER_COLORS


def test_parse_llm_output_basic():
    raw = json.dumps({
        "title": "Test List",
        "categories": [
            {"tier_name": "S", "items": [{"name": "Apple", "search_keyword": "Apple logo"}]},
            {"tier_name": "A", "items": [{"name": "Samsung", "search_keyword": "Samsung logo"}]},
        ],
    })
    result = _parse_llm_output(raw)
    assert result.title == "Test List"
    assert len(result.categories) == 2
    assert result.categories[0].tier_name == "S"
    assert result.categories[0].items[0].name == "Apple"
    assert result.categories[0].color == TIER_COLORS[0]


def test_parse_llm_output_strips_markdown():
    raw = '```json\n{"title":"T","categories":[]}\n```'
    result = _parse_llm_output(raw)
    assert result.title == "T"
    assert len(result.categories) == 0


def test_assign_colors_wraps_around():
    cats = [{"tier_name": chr(65 + i), "items": []} for i in range(10)]
    colored = _assign_colors(cats)
    assert colored[0]["color"] == TIER_COLORS[0]
    assert colored[8]["color"] == TIER_COLORS[0]  # wraps around


def test_regex_fallback_basic():
    text = "S tier: Apple, Samsung\nA tier: Google, OnePlus"
    result = _regex_fallback(text)
    assert len(result.categories) == 2
    assert result.categories[0].tier_name == "S"
    assert len(result.categories[0].items) == 2
    assert result.categories[1].tier_name == "A"
    assert len(result.categories[1].items) == 2


def test_regex_fallback_no_tier_labels():
    text = "Apple\nSamsung"
    result = _regex_fallback(text)
    # Items go into default tier "A"
    assert len(result.categories) == 1
    assert result.categories[0].tier_name == "A"
    assert len(result.categories[0].items) == 2
