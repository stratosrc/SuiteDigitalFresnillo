"""Pure helpers for the virtual personnel viewport."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VirtualWindow:
    """Describe the records represented by a fixed-size pool of row widgets."""

    start: int
    stop: int
    total: int

    @property
    def first_fraction(self) -> float:
        if self.total <= 0:
            return 0.0
        return self.start / self.total

    @property
    def last_fraction(self) -> float:
        if self.total <= 0:
            return 1.0
        return self.stop / self.total


def virtual_window(total: int, capacity: int, requested_start: int) -> VirtualWindow:
    """Clamp a requested window to the available records."""
    safe_total = max(0, total)
    safe_capacity = max(1, capacity)
    maximum_start = max(0, safe_total - safe_capacity)
    start = max(0, min(requested_start, maximum_start))
    stop = min(safe_total, start + safe_capacity)
    return VirtualWindow(start=start, stop=stop, total=safe_total)


def start_from_fraction(total: int, capacity: int, fraction: float) -> int:
    """Translate a scrollbar ``moveto`` fraction to a valid window start."""
    bounded_fraction = max(0.0, min(float(fraction), 1.0))
    requested_start = round(max(0, total) * bounded_fraction)
    return virtual_window(total, capacity, requested_start).start


__all__ = ["VirtualWindow", "start_from_fraction", "virtual_window"]
