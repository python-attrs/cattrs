"""Loading of attrs classes."""
from attr import asdict, astuple, fields, make_class
from hypothesis import assume, given

from typing import Union

from . import simple_classes, simple_attrs


@given(simple_classes())
def test_structure_simple_from_dict(converter, cl_and_vals):
    # type: (Converter, Any) -> None
    """Test structuring non-nested attrs classes dumped with asdict."""
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = asdict(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_attrs(defaults=True))
def test_structure_simple_from_dict_default(converter, cl_and_vals):
    """Test structuring non-nested attrs classes with default value."""
    a, _ = cl_and_vals
    cl = make_class("HypClass", {"a": a})
    obj = cl()
    loaded = converter.structure({}, cl)
    assert obj == loaded


@given(simple_classes())
def test_roundtrip(converter, cl_and_vals):
    # type: (Converter, Any) -> None
    """We dump the class, then we load it."""
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = converter.unstructure(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_structure_tuple(converter, cl_and_vals):
    # type: (Converter, Any) -> None
    """Test loading from a tuple, by registering the loader."""
    cl, vals = cl_and_vals
    converter.register_structure_hook(cl, converter.structure_attrs_fromtuple)
    obj = cl(*vals)

    dumped = astuple(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_structure_union(converter, cl_and_vals_a, cl_and_vals_b):
    """Structuring of automatically-disambiguable unions works."""
    # type: (Converter, Any, Any) -> None
    cl_a, vals_a = cl_and_vals_a
    cl_b, vals_b = cl_and_vals_b
    a_field_names = {a.name for a in fields(cl_a)}
    b_field_names = {a.name for a in fields(cl_b)}
    assume(a_field_names)
    assume(b_field_names)

    common_names = a_field_names & b_field_names
    if len(a_field_names) > len(common_names):
        obj = cl_a(*vals_a)
        dumped = asdict(obj)
        res = converter.structure(dumped, Union[cl_a, cl_b])
        assert isinstance(res, cl_a)
        assert obj == res


@given(simple_classes(), simple_classes())
def test_structure_union_explicit(converter, cl_and_vals_a, cl_and_vals_b):
    """Structuring of manually-disambiguable unions works."""
    # type: (Converter, Any, Any) -> None
    cl_a, vals_a = cl_and_vals_a
    cl_b, vals_b = cl_and_vals_b

    def dis(obj, _):
        return converter.structure(obj, cl_a)

    converter.register_structure_hook(Union[cl_a, cl_b], dis)

    inst = cl_a(*vals_a)

    assert inst == converter.structure(converter.unstructure(inst),
                                       Union[cl_a, cl_b])
