"""Simple life event model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LifeEvent:
    year: int
    event_type: str
    amount: float = 0.0
    notes: str = ""
