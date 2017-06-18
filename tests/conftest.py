import platform

import pytest

from hypothesis import HealthCheck, settings

from cattr import Converter


@pytest.fixture()
def converter():
    return Converter()


if platform.python_implementation() == 'PyPy':
    settings.default.suppress_health_check.append(HealthCheck.too_slow)
