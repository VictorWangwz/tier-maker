from __future__ import annotations

import json
import logging
import re

from langchain_openai import ChatOpenAI

from app.config import settings
from app.models import TierCategory, TierItem, TierListResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a data extraction assistant for tier lists. The user will describe items and their \
tier rankings. Extract this into a JSON object matching this exact schema:

{
  "title": "a short descriptive title for the tier list",
  "categories": [
    {
      "tier_name": "the tier label, e.g. S, A, B, C, D, F, or any custom name the user gives",
      "items": [
        {
          "name": "the item name",
          "search_keyword": "an optimized search query likely to return a good icon or product photo, e.g. 'Apple logo' or 'iPhone 15 product shot'"
        }
      ]
    }
  ]
}

Rules:
- If the user does not provide a title, generate a brief fitting one.
- Preserve the order of tiers as the user specifies them.
- For each item, generate a search_keyword that would yield a good image result.
- Include all tiers the user mentions, even if some are empty.
- Return ONLY valid JSON, no markdown fences or extra text."""

# Default tier colors assigned by position
TIER_COLORS = [
    "#FF7F7F",  # Red
    "#FFBF7F",  # Orange
    "#FFDF7F",  # Yellow
    "#BFFF7F",  # Green
    "#7FBFFF",  # Blue
    "#7F7FFF",  # Indigo
    "#BF7FFF",  # Purple
    "#FF7FBF",  # Pink
]


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.1,
        model_kwargs={"response_format": {"type": "json_object"}},
    )


def _assign_colors(categories: list[dict]) -> list[dict]:
    for i, cat in enumerate(categories):
        cat["color"] = TIER_COLORS[i % len(TIER_COLORS)]
    return categories


def _parse_llm_output(raw: str) -> TierListResult:
    # Strip markdown fences if the LLM wraps output in them
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    data["categories"] = _assign_colors(data.get("categories", []))
    return TierListResult.model_validate(data)


def _regex_fallback(text: str) -> TierListResult:
    """Attempt a rough parse when the LLM fails to produce valid JSON."""
    categories: dict[str, list[TierItem]] = {}
    current_tier = "A"
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tier_match = re.match(r"^(?:tier\s*)?([SsA-Fa-f])\s*(?:tier)?\s*[:\-—]\s*(.*)", line, re.IGNORECASE)
        if tier_match:
            current_tier = tier_match.group(1).upper()
            rest = tier_match.group(2).strip()
            categories.setdefault(current_tier, [])
            if rest:
                for item_name in re.split(r"[,;、]", rest):
                    item_name = item_name.strip()
                    if item_name:
                        categories[current_tier].append(
                            TierItem(name=item_name, search_keyword=f"{item_name} logo")
                        )
        else:
            items = re.split(r"[,;、]", line)
            categories.setdefault(current_tier, [])
            for item_name in items:
                item_name = item_name.strip()
                if item_name:
                    categories[current_tier].append(
                        TierItem(name=item_name, search_keyword=f"{item_name} logo")
                    )

    cat_list = [
        TierCategory(
            tier_name=name,
            color=TIER_COLORS[i % len(TIER_COLORS)],
            items=items,
        )
        for i, (name, items) in enumerate(categories.items())
    ]
    return TierListResult(title="Tier List", categories=cat_list)


def parse_tier_list(text: str) -> TierListResult:
    llm = _get_llm()
    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=text),
        ])
        raw = response.content or ""
        return _parse_llm_output(raw)
    except json.JSONDecodeError as e:
        logger.warning("LLM returned invalid JSON, using regex fallback: %s", e)
        return _regex_fallback(text)
    except Exception as e:
        logger.warning("LLM call failed (%s), using regex fallback", e)
        return _regex_fallback(text)
