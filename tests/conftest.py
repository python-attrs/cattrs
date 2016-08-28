import pytest

from cattrs import Converter


@pytest.fixture()
def converter():
    return Converter()