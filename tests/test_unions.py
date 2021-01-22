from typing import Type, Union

import attr
from hypothesis import given
from hypothesis.strategies import sampled_from

from cattr.converters import Converter, GenConverter


@given(sampled_from([Converter, GenConverter]))
def test_custom_union_toplevel_roundtrip(cls: Type[Converter]):
    """
    Test custom code union handling.

    We override union unstructuring to add the class type, and union structuring
    to use the class type.
    """
    c = cls()

    @attr.define
    class A:
        a: int

    @attr.define
    class B:
        a: int

    c.register_unstructure_hook(
        Union[A, B],
        lambda o: {"_type": o.__class__.__name__, **c.unstructure(o)},
    )
    c.register_structure_hook(
        Union[A, B], lambda o, t: c.structure(o, A if o["_type"] == "A" else B)
    )

    inst = B(1)
    unstructured = c.unstructure(inst, unstructure_as=Union[A, B])
    assert unstructured["_type"] == "B"

    assert c.structure(unstructured, Union[A, B]) == inst


@given(sampled_from([Converter, GenConverter]))
def test_custom_union_clsfield_roundtrip(cls: Type[Converter]):
    """
    Test custom code union handling.

    We override union unstructuring to add the class type, and union structuring
    to use the class type.
    """
    c = cls()

    @attr.define
    class A:
        a: int

    @attr.define
    class B:
        a: int

    @attr.define
    class C:
        f: Union[A, B]

    c.register_unstructure_hook(
        Union[A, B],
        lambda o: {"_type": o.__class__.__name__, **c.unstructure(o)},
    )
    c.register_structure_hook(
        Union[A, B], lambda o, t: c.structure(o, A if o["_type"] == "A" else B)
    )

    inst = C(A(1))
    unstructured = c.unstructure(inst)
    assert unstructured["f"]["_type"] == "A"

    assert c.structure(unstructured, C) == inst
