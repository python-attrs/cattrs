from typing import Optional
import attr

from .nested_a import InnerA


@attr.define
class InnerB:
    a: InnerA
    b: InnerA
    c: InnerA
    d: Optional[InnerA] = None
