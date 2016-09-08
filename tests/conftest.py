import pytest

from cattr import Converter


@pytest.fixture()
def converter():
    return Converter()
