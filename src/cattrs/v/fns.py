from typing import Never


def invalid_value(val) -> Never:
    """Called with an invalid value when a value validator returns `False`."""
    raise ValueError(f"Validation failed for {val}")
