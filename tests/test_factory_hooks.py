"""Tests for the factory hooks documentation."""

from attr import define, fields, has

from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override


def to_camel_case(snake_str):
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def test_snake_to_camel(converter_cls):
    @define
    class Inner:
        a_snake_case_int: int
        a_snake_case_float: float
        a_snake_case_str: str

    @define
    class Outer:
        a_snake_case_inner: Inner

    converter = converter_cls()

    def unstructure_adapt_to_camel_case(type):
        return make_dict_unstructure_fn(
            type,
            converter,
            **{a.name: override(rename=to_camel_case(a.name)) for a in fields(type)},
        )

    converter.register_unstructure_hook_factory(has, unstructure_adapt_to_camel_case)

    original = Outer(Inner(0, 0.0, "str"))
    unstructured = converter.unstructure(original)

    assert unstructured == {
        "aSnakeCaseInner": {
            "aSnakeCaseInt": 0,
            "aSnakeCaseFloat": 0.0,
            "aSnakeCaseStr": "str",
        }
    }

    def structure_adapt_to_camel_case(type):
        overrides = {
            a.name: override(rename=to_camel_case(a.name)) for a in fields(type)
        }
        return make_dict_structure_fn(type, converter, **overrides)

    converter.register_structure_hook_factory(has, structure_adapt_to_camel_case)

    structured = converter.structure(unstructured, Outer)
    assert structured == original
