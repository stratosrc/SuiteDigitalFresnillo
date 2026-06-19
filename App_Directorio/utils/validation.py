from datetime import datetime


DATE_FORMAT = "%d/%m/%Y"
DATE_INPUT_LENGTH = 10


def is_date_input_prefix(value: str) -> bool:
    if len(value) > DATE_INPUT_LENGTH:
        return False

    for index, character in enumerate(value):
        if index in (2, 5):
            if character != "/":
                return False
            continue
        if not character.isdigit():
            return False

    return True


def is_valid_date(value: str) -> bool:
    if len(value) != DATE_INPUT_LENGTH or not is_date_input_prefix(value):
        return False
    try:
        parsed = datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return False
    return parsed.strftime(DATE_FORMAT) == value


__all__ = [
    "DATE_FORMAT",
    "DATE_INPUT_LENGTH",
    "is_date_input_prefix",
    "is_valid_date",
]
