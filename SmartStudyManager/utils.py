"""Small validation and formatting helpers shared by the application."""

from __future__ import annotations

from datetime import datetime


def is_valid_date(value: str) -> bool:
    """Return True for an ISO date such as 2026-09-24."""
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def display_hours(minutes: int | float) -> str:
    """Turn minutes into a compact, friendly hour value."""
    return f"{float(minutes) / 60:.1f} hrs"


def attendance_percentage(total: int, attended: int) -> float:
    """Calculate attendance safely, including the no-classes-yet case."""
    return (attended * 100 / total) if total else 0.0
