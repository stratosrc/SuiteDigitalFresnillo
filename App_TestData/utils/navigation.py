"""Pure page navigation helpers."""


def get_adjacent_page_index(current_page: int, total_pages: int, action: str) -> int:
    """Return the next valid page index for the requested direction."""
    if total_pages <= 0:
        return current_page
    if action == "prev":
        return max(0, current_page - 1)
    if action == "next":
        return min(total_pages - 1, current_page + 1)
    return current_page


def parse_page_number(raw_value: str) -> int:
    """Parse a 1-based page number entered by the user."""
    return int(raw_value)


def to_page_index(page_number: int) -> int:
    """Convert a 1-based page number into a 0-based index."""
    return page_number - 1


def is_valid_page_index(page_index: int, total_pages: int) -> bool:
    """Return whether a 0-based page index exists in the document."""
    return 0 <= page_index < total_pages
