"""Pure válidation helpers used by the UI layer."""

from __future__ import annotations



def parse_int(value: str) -> int:
    """Convert a text value into an integer."""
    return int(value)


def is_within_range(value: int, minimum: int, maximum: int) -> bool:
    """Return whether a numeric value belongs to the accepted interval."""
    return minimum <= value <= maximum


def parse_bounded_int(value: str, minimum: int, maximum: int) -> int:
    """Parse an integer and válidate its allowed range."""
    parsed_value = parse_int(value)
    if not is_within_range(parsed_value, minimum, maximum):
        raise ValueError("Value out of range")
    return parsed_value


def parse_bounded_pair(
    first_value: str,
    second_value: str,
    minimum: int,
    maximum: int,
) -> tuple[int, int]:
    """Parse and válidate two bounded integer values."""
    return (
        parse_bounded_int(first_value, minimum, maximum),
        parse_bounded_int(second_value, minimum, maximum),
    )
