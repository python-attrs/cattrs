"""Loading of attrs classes."""
from typing import Union

from attr import NOTHING, Factory, asdict, astuple, fields
from hypothesis import assume, given
from hypothesis.strategies import data, lists, sampled_from

from cattr.converters import Converter

from . import simple_classes


@given(simple_classes())
def test_structure_simple_from_dict(converter, cl_and_vals):
    """Test structuring non-nested attrs classes dumped with asdict."""
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = asdict(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=True, min_attrs=1, frozen=False), data())
def test_structure_simple_from_dict_default(converter, cl_and_vals, data):
    """Test structuring non-nested attrs classes with default value."""
    cl, vals = cl_and_vals
    obj = cl(*vals)
    attrs_with_defaults = [a for a in fields(cl) if a.default is not NOTHING]
    to_remove = data.draw(
        lists(elements=sampled_from(attrs_with_defaults), unique=True)
    )

    for a in to_remove:
        if isinstance(a.default, Factory):
            setattr(obj, a.name, a.default.factory())
        else:
            setattr(obj, a.name, a.default)

    dumped = asdict(obj)

    for a in to_remove:
        del dumped[a.name]

    assert obj == converter.structure(dumped, cl)


@given(simple_classes())
def test_roundtrip(cl_and_vals):
    """We dump the class, then we load it."""
    converter = Converter()
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = converter.unstructure(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_structure_tuple(converter, cl_and_vals):
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


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_structure_union_none(converter, cl_and_vals_a, cl_and_vals_b):
    """Structuring of automatically-disambiguable unions works."""
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
        res = converter.structure(dumped, Union[cl_a, cl_b, None])
        assert isinstance(res, cl_a)
        assert obj == res

    assert converter.structure(None, Union[cl_a, cl_b, None]) is None


@given(simple_classes(), simple_classes())
def test_structure_union_explicit(converter, cl_and_vals_a, cl_and_vals_b):
    """Structuring of manually-disambiguable unions works."""
    cl_a, vals_a = cl_and_vals_a
    cl_b, vals_b = cl_and_vals_b

    def dis(obj, _):
        return converter.structure(obj, cl_a)

    converter.register_structure_hook(Union[cl_a, cl_b], dis)

    inst = cl_a(*vals_a)

    assert inst == converter.structure(
        converter.unstructure(inst), Union[cl_a, cl_b]
    )
