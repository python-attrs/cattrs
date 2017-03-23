"""Loading of attrs classes."""
from attr import asdict, astuple, fields
from hypothesis import assume, given

from cattr import Converter
from cattr._compat import Union

from . import simple_classes


@given(simple_classes())
def test_structure_simple_from_dict(converter, cl_and_vals):
    """Test structuring non-nested attrs classes dumped with asdict."""
    # type: (Converter, Any) -> None
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = asdict(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_roundtrip(converter, cl_and_vals):
    """We dump the class, then we load it."""
    # type: (Converter, Any) -> None
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = converter.unstructure(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_structure_tuple(converter, cl_and_vals):
    """Test loading from a tuple, by registering the loader."""
    # type: (Converter, Any) -> None
    cl, vals = cl_and_vals
    converter.register_structure_hook(cl, converter.structure_attrs_fromtuple)
    obj = cl(*vals)

    dumped = astuple(obj)
    loaded = converter.structure(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_structure_union(converter, cl_and_vals_a, cl_and_vals_b):
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
