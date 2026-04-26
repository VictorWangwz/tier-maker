from __future__ import annotations

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def select_template(num_tiers: int) -> Path:
    if num_tiers <= 3:
        name = "compact.html"
    elif num_tiers <= 6:
        name = "standard.html"
    else:
        name = "massive.html"
    return TEMPLATES_DIR / name
