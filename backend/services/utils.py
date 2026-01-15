"""Shared utility functions for the Care Docs API."""

from datetime import datetime, timezone


def to_utc_iso(value: datetime) -> str:
    """Convert a datetime to UTC ISO 8601 string format.

    Args:
        value: A datetime object (naive or aware)

    Returns:
        ISO 8601 formatted string in UTC timezone
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()
