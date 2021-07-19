from __future__ import annotations
from typing import TYPE_CHECKING
import attr

if TYPE_CHECKING:
    from .nested_c import InnerC


@attr.define
class InnerD:
    a: InnerC
    b: InnerC
    c: InnerC
    d: InnerC
