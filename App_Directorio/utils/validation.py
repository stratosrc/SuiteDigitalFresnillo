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
    return len(value) == DATE_INPUT_LENGTH and is_date_input_prefix(value)


__all__ = [
    "DATE_FORMAT",
    "DATE_INPUT_LENGTH",
    "is_date_input_prefix",
    "is_valid_date",
]
