from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TierItem(BaseModel):
    name: str
    search_keyword: str
    image_url: Optional[str] = None


class TierCategory(BaseModel):
    tier_name: str
    color: str
    items: list[TierItem]


class TierListResult(BaseModel):
    title: str
    categories: list[TierCategory]


class GenerateRequest(BaseModel):
    text: str


class GenerateResponse(BaseModel):
    image_url: str
    tier_data: TierListResult
