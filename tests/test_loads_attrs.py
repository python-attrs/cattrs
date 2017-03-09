"""Loading of attrs classes."""
from attr import asdict, astuple, fields
from hypothesis import assume, given

from cattr import Converter
from cattr._compat import Union

from . import simple_classes


@given(simple_classes())
def test_load_simple_from_dict(converter: Converter, cl_and_vals):
    """Test loading non-nested attrs classes dumped with asdict."""
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = asdict(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_roundtrip(converter: Converter, cl_and_vals):
    """We dump the class, then we load it."""
    cl, vals = cl_and_vals
    obj = cl(*vals)

    dumped = converter.dumps(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded


@given(simple_classes())
def test_load_tuple(converter: Converter, cl_and_vals):
    """Test loading from a tuple, by registering the loader."""
    cl, vals = cl_and_vals
    converter.register_loads_hook(cl, converter.loads_attrs_fromtuple)
    obj = cl(*vals)

    dumped = astuple(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded


@given(simple_classes(defaults=False), simple_classes(defaults=False))
def test_loads_union(converter: Converter, cl_and_vals_a, cl_and_vals_b):
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
        res = converter.loads(dumped, Union[cl_a, cl_b])
        assert isinstance(res, cl_a)
        assert obj == res
