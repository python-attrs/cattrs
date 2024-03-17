from pytest import fixture

from cattrs import Converter


@fixture
def c() -> Converter:
    """We need only converters with detailed_validation=True."""
    return Converter()
