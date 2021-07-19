from typing import Optional
import attr

from .nested_b import InnerB


@attr.define
class InnerC:
    a: InnerB
    b: InnerB
    c: InnerB
    d: InnerB
