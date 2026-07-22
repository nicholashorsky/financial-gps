"""Neutral user-facing guidance for supported FIRE variants."""

from __future__ import annotations


FIRE_VARIANT_GUIDANCE = {
    "lean": {
        "label": "Lean FIRE",
        "definition": "Retirement supported by a deliberately lower-cost lifestyle focused on essential spending.",
        "impact": "Usually means a lower spending target, but less room for optional expenses or unexpected costs.",
    },
    "coast": {
        "label": "Coast FIRE",
        "definition": "Existing retirement savings are left to grow while current income covers today's expenses.",
        "impact": "Focuses on whether invested savings can reach the future target with reduced or no new contributions.",
    },
    "barista": {
        "label": "Barista FIRE",
        "definition": "Part-time or lower-intensity work continues to cover part of retirement spending.",
        "impact": "Requires ongoing earned income to be entered separately; that income can reduce required withdrawals.",
    },
    "fat": {
        "label": "Fat FIRE",
        "definition": "Retirement supported by a higher spending target with more room for optional expenses.",
        "impact": "Usually requires a larger portfolio, more saving, a later target date, or some combination of these.",
    },
}

FIRE_VARIANTS = tuple(FIRE_VARIANT_GUIDANCE)


def fire_variant_label(variant: str) -> str:
    """Return the display label for a stored FIRE variant value."""
    return FIRE_VARIANT_GUIDANCE[variant]["label"]
