from typing import Annotated, Union

import attrs
import pytest

from cattrs.gen._shared import get_fields_annotated_by


class NotThere: ...


class IgnoreMe:
    def __init__(self, why: Union[str, None] = None):
        self.why = why


class FindMe:
    def __init__(self, taint: str):
        self.taint = taint


class EmptyClassExample:
    pass


class PureClassExample:
    id: Annotated[int, FindMe("red")]
    name: Annotated[str, FindMe]


class MultipleAnnotationsExample:
    id: Annotated[int, FindMe("red"), IgnoreMe()]
    name: Annotated[str, IgnoreMe()]
    surface: Annotated[str, IgnoreMe("sorry"), FindMe("shiny")]


@attrs.define
class AttrsClassExample:
    id: int = attrs.field(default=0)
    color: Annotated[str, FindMe("blue")] = attrs.field(default="red")
    config: Annotated[dict, FindMe("required")] = attrs.field(factory=dict)


class PureClassInheritanceExample(PureClassExample):
    include: dict
    exclude: Annotated[dict, FindMe("boring things")]
    extras: Annotated[dict, FindMe]


@pytest.mark.parametrize(
    "klass,expected",
    [
        (EmptyClassExample, {}),
        (PureClassExample, {"id": isinstance}),
        (AttrsClassExample, {"color": isinstance, "config": isinstance}),
        (MultipleAnnotationsExample, {"id": isinstance, "surface": isinstance}),
        (PureClassInheritanceExample, {"id": isinstance, "exclude": isinstance}),
    ],
)
@pytest.mark.parametrize("instantiate", [True, False])
def test_gets_annotated_types(klass, expected, instantiate: bool):
    annotated = get_fields_annotated_by(
        klass, FindMe("irrelevant") if instantiate else FindMe
    )

    assert set(annotated.keys()) == set(
        expected.keys()
    ), "Too many or too few annotations"
    assert all(
        assertion_func(annotated[field_name], FindMe)
        for field_name, assertion_func in expected.items()
    ), "Unexpected type of annotation"


def test_empty_result_for_missing_annotation():
    annotated = get_fields_annotated_by(MultipleAnnotationsExample, NotThere)
    assert not annotated, "No annotation should be found."
