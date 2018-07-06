import platform

import pytest

from hypothesis import HealthCheck, settings

from cattr import Converter


@pytest.fixture()
def converter():
    return Converter()


settings.default.suppress_health_check.append(HealthCheck.too_slow)
