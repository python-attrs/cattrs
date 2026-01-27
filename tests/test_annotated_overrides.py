from dataclasses import dataclass
from typing import Annotated, NamedTuple, TypedDict

from attrs import define

from cattrs import Converter
from cattrs._compat import NotRequired
from cattrs.cols import (
    is_namedtuple,
    namedtuple_dict_structure_factory,
    namedtuple_dict_unstructure_factory,
)
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override
from cattrs.gen.typeddicts import make_dict_structure_fn as make_td_structure_fn
from cattrs.gen.typeddicts import make_dict_unstructure_fn as make_td_unstructure_fn


def test_annotated_override_attrs(genconverter: Converter):
    """Annotated overrides work for attrs classes."""

    @define
    class A:
        a: Annotated[int, override(rename="b")]
        c: Annotated[int, override(omit=True)] = 1
        d: Annotated[int, override(rename="e")] = 2

    instance = A(1)
    # 'a' is renamed to 'b', 'c' is omitted. 'd' is default so present as 'e'
    assert genconverter.unstructure(instance) == {"b": 1, "e": 2}

    assert genconverter.structure({"b": 1, "e": 2}, A) == A(1)


def test_annotated_override_dataclasses(genconverter: Converter):
    """Annotated overrides work for dataclasses."""

    @dataclass
    class A:
        a: Annotated[int, override(rename="b")]
        c: Annotated[int, override(omit=True)] = 1

    instance = A(1)
    assert genconverter.unstructure(instance) == {"b": 1}

    assert genconverter.structure({"b": 1}, A) == A(1)


def test_annotated_override_typeddict(genconverter: Converter):
    """Annotated overrides work for TypedDicts."""

    class TD(TypedDict):
        a: Annotated[int, override(rename="b")]
        c: Annotated[int, override(omit=True)]

    instance: TD = {"a": 1, "c": 2}

    assert genconverter.unstructure(instance, TD) == {"b": 1}

    # Let's simplify and just test rename for now to avoid required field issues with omit.
    class TD2(TypedDict):
        a: Annotated[int, override(rename="b")]

    inst2: TD2 = {"a": 1}
    assert genconverter.unstructure(inst2, TD2) == {"b": 1}
    assert genconverter.structure({"b": 1}, TD2) == {"a": 1}


def test_annotated_override_namedtuple(genconverter: Converter):
    """Annotated overrides work for NamedTuples using dict factories."""

    # We need to register the dict factories for NamedTuples
    genconverter.register_unstructure_hook_factory(
        is_namedtuple, namedtuple_dict_unstructure_factory
    )
    genconverter.register_structure_hook_factory(
        is_namedtuple, namedtuple_dict_structure_factory
    )

    class NT(NamedTuple):
        a: Annotated[int, override(rename="b")]
        c: Annotated[int, override(omit=True)] = 1

    instance = NT(1)
    assert genconverter.unstructure(instance) == {"b": 1}
    assert genconverter.structure({"b": 1}, NT) == NT(1)


def test_annotated_override_precedence(genconverter: Converter):
    """Test that explicit kwargs override Annotated metadata."""

    @define
    class A:
        a: Annotated[int, override(rename="b")]

    # Override the rename back to 'a' explicitly
    unstructure_fn = make_dict_unstructure_fn(A, genconverter, a=override(rename="a"))
    genconverter.register_unstructure_hook(A, unstructure_fn)

    assert genconverter.unstructure(A(1)) == {"a": 1}

    # # Structure override
    structure_fn = make_dict_structure_fn(A, genconverter, a=override(rename="a"))
    genconverter.register_structure_hook(A, structure_fn)

    assert genconverter.structure({"a": 1}, A) == A(1)


def test_annotated_override_hooks(genconverter: Converter):
    """struct_hook and unstruct_hook work in Annotated."""

    def double_hook(v):
        return v * 2

    def half_hook(v, _):
        return v // 2

    @define
    class A:
        a: Annotated[int, override(unstruct_hook=double_hook, struct_hook=half_hook)]

    assert genconverter.unstructure(A(10)) == {"a": 20}
    assert genconverter.structure({"a": 20}, A) == A(10)


def test_annotated_override_omit_if_default(genconverter: Converter):
    """omit_if_default works in Annotated."""

    @define
    class A:
        a: Annotated[int, override(omit_if_default=True)] = 0
        b: int = 1

    # a matches default, should be omitted. b matches default but no override, should stay (default behavior is to keep)
    assert genconverter.unstructure(A()) == {"b": 1}
    assert genconverter.unstructure(A(a=1)) == {"a": 1, "b": 1}


def test_overrides_attribute_populated(genconverter: Converter):
    """The .overrides attribute is correctly populated."""

    @dataclass
    class A:
        a: Annotated[int, override(rename="b")]
        c: Annotated[int, override(omit=True)] = 1

    # Test dataclasses (make_dict_unstructure_fn)
    unstruct_hook = make_dict_unstructure_fn(A, genconverter)
    assert unstruct_hook.overrides == {
        "a": override(rename="b"),
        "c": override(omit=True),
    }

    struct_hook = make_dict_structure_fn(A, genconverter)
    assert struct_hook.overrides == {
        "a": override(rename="b"),
        "c": override(omit=True),
    }

    class TD(TypedDict):
        a: Annotated[int, override(rename="b")]
        c: NotRequired[Annotated[int, override(rename="d")]]

    td_unstruct_hook = make_td_unstructure_fn(TD, genconverter)
    assert td_unstruct_hook.overrides == {
        "a": override(rename="b"),
        "c": override(rename="d"),
    }

    td_struct_hook = make_td_structure_fn(TD, genconverter)
    assert td_struct_hook.overrides == {
        "a": override(rename="b"),
        "c": override(rename="d"),
    }

    # Test Precedence (explicit should win and be in overrides)
    @dataclass
    class B:
        a: Annotated[int, override(rename="b")]

    hook_explicit = make_dict_unstructure_fn(B, genconverter, a=override(rename="c"))
    assert hook_explicit.overrides["a"].rename == "c"
