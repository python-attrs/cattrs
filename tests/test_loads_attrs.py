"""Loading of attrs classes."""
from attr import asdict, astuple
from hypothesis import given

from cattr import Converter

from . import simple_classes


@given(simple_classes)
def test_load_simple_from_dict(converter: Converter, cl):
    """Test loading non-nested attrs classes dumped with asdict."""
    obj = cl()

    dumped = asdict(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded


@given(simple_classes)
def test_roundtrip(converter: Converter, cl):
    """We dump the class, then we load it."""
    obj = cl()

    dumped = converter.dumps(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded


@given(simple_classes)
def test_load_tuple(converter: Converter, cl):
    """Test loading from a tuple, by registering the loader."""
    converter.register_loads_hook(cl, converter.loads_attrs_fromtuple)
    obj = cl()

    dumped = astuple(obj)
    loaded = converter.loads(dumped, cl)

    assert obj == loaded
