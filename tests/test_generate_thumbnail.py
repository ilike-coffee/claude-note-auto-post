import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_thumbnail import _resolve_tier, PALETTES


def test_resolve_tier_returns_tier_for_matching_day():
    topics_data = {
        "topics": [
            {"day": 1, "tier": "初級"},
            {"day": 31, "tier": "中級"},
            {"day": 51, "tier": "上級"},
        ]
    }
    assert _resolve_tier(topics_data, 31) == "中級"
    assert _resolve_tier(topics_data, 51) == "上級"


def test_resolve_tier_defaults_to_shokyu_when_day_not_found():
    topics_data = {"topics": [{"day": 1, "tier": "初級"}]}
    assert _resolve_tier(topics_data, 999) == "初級"


def test_resolve_tier_defaults_to_shokyu_when_tier_field_missing():
    topics_data = {"topics": [{"day": 1}]}
    assert _resolve_tier(topics_data, 1) == "初級"


def test_all_tiers_have_complete_palette_entries():
    for tier in ["初級", "中級", "上級"]:
        assert tier in PALETTES
        assert set(PALETTES[tier].keys()) == {"main", "accent", "dark"}
