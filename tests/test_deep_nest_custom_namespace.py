import pytest

from cattr.preconf.pyyaml import make_converter as yaml_converter
import attr
import yaml
import io

from .nested_type_check_test.nested_a import InnerA
from .nested_type_check_test.nested_b import InnerB
from .nested_type_check_test.nested_c import InnerC
from .nested_type_check_test.nested_d import InnerD
from .nested_type_check_test.nested_e import InnerE
from .nested_type_check_test.nested_o import Outer


# make False first as the caching of yaml converter causes False to pass
# if second
@pytest.mark.parametrize("register_namespace", [False, True])
def test_unstruct_attrs_deep_nest(register_namespace):
    c = yaml_converter()
    if register_namespace:
        c.register_namespace(globals())
    make_inner_a = lambda: InnerA(1, 1.0, "one", "one".encode())
    make_inner_b = lambda: InnerB(*[make_inner_a() for _ in range(4)])
    make_inner_c = lambda: InnerC(*[make_inner_b() for _ in range(4)])
    make_inner_d = lambda: InnerD(*[make_inner_c() for _ in range(4)])
    make_inner_e = lambda: InnerE(*[make_inner_d() for _ in range(4)])

    inst = Outer(*[make_inner_e() for _ in range(4)])
    unstruct = c.unstructure(inst)
    b = c.structure(unstruct, Outer)

    assert inst == b
