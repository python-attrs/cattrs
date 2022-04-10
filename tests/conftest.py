import pytest
from hypothesis import HealthCheck, settings

from cattrs import BaseConverter, Converter


@pytest.fixture(params=(BaseConverter, Converter))
def converter(request):
    return request.param()


settings.register_profile(
    "tests", suppress_health_check=(HealthCheck.too_slow,), deadline=None
)

settings.load_profile("tests")
