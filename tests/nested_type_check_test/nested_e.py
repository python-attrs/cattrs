from __future__ import annotations
from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from .nested_d import InnerD


@attr.define
class InnerE:
    a: InnerD
    b: InnerD
    c: InnerD
    d: InnerD
