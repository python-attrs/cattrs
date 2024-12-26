import os
from typing import Literal

from hypothesis import HealthCheck, settings
from hypothesis.strategies import just, one_of
from typing_extensions import TypeAlias

from cattrs import UnstructureStrategy

settings.register_profile(
    "CI", settings(suppress_health_check=[HealthCheck.too_slow]), deadline=None
)

if "CI" in os.environ:  # pragma: nocover
    settings.load_profile("CI")

unstructure_strats = one_of(just(s) for s in UnstructureStrategy)

FeatureFlag: TypeAlias = Literal["always", "never", "sometimes"]
