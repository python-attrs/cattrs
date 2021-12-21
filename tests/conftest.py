import pytest
from hypothesis import HealthCheck, settings

from cattrs import Converter


@pytest.fixture()
def converter():
    return Converter()


settings.register_profile(
    "tests", suppress_health_check=(HealthCheck.too_slow,), deadline=None
)

settings.load_profile("tests")
