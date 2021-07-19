from typing import Optional
import attr


@attr.define
class InnerA:
    a: int
    b: float
    c: str
    d: bytes
    e: Optional[int] = None
