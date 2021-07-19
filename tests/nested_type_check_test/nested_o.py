from __future__ import annotations
from typing import TYPE_CHECKING
import attr

if TYPE_CHECKING:
    from .nested_e import InnerE


@attr.define
class Outer:
    a: InnerE
    b: InnerE
    c: InnerE
    d: InnerE
