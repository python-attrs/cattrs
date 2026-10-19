# Structuring Types

These tests exercise the static return types for the structuring APIs.

## Global structure returns attrs instances

```python
from attrs import define

from cattrs import structure


@define
class User:
    id: int
    name: str


user = structure({"id": 1, "name": "Ada"}, User)
reveal_type(user)  # revealed: test_snippet.User

name: str = user.name
```

## Converter structure returns dataclass instances

```python
from dataclasses import dataclass

from cattrs import Converter


@dataclass
class Point:
    x: int
    y: int


converter = Converter()
point = converter.structure({"x": 1, "y": 2}, Point)
reveal_type(point)  # revealed: test_snippet.Point

x: int = point.x
```

## Converter structure returns TypedDicts

```python
from typing import TypedDict

from cattrs import Converter


class Movie(TypedDict):
    title: str
    year: int


converter = Converter()
movie = converter.structure({"title": "Alien", "year": 1979}, Movie)
reveal_type(movie)  # revealed: TypedDict(test_snippet.Movie, {"title": str, "year": int})

title: str = movie["title"]
```

## Converter structure returns homogeneous tuples

```python
from cattrs import Converter


converter = Converter()
numbers = converter.structure([1, 2, 3], tuple[int, ...])
reveal_type(numbers)  # revealed: tuple[int, ...]

first: int = numbers[0]
```

## Converter structure returns heterogeneous tuples

```python
from cattrs import Converter


converter = Converter()
row = converter.structure(["Ada", 37, True], tuple[str, int, bool])
reveal_type(row)  # revealed: tuple[str, int, bool]

name: str = row[0]
age: int = row[1]
active: bool = row[2]
```

## Structure result participates in type checking

```python
from cattrs import Converter


converter = Converter()

value: int = converter.structure("1", int)
bad: str = converter.structure("1", int)  # mypy-error: [assignment]
```

## Hook factory decorators preserve factory types

```python
from collections.abc import Callable
from typing import Any

from cattrs import Converter


converter = Converter()


def accepts_int(cl: Any) -> bool:
    return cl is int


@converter.register_unstructure_hook_factory(accepts_int)
def unstructure_factory(cl: type[int]) -> Callable[[int], str]:
    return str


@converter.register_structure_hook_factory(accepts_int)
def structure_factory(cl: type[int]) -> Callable[[str, type[int]], int]:
    return lambda value, _: int(value)


reveal_type(unstructure_factory)  # revealed: def (cl: type[int]) -> def (int) -> str
reveal_type(structure_factory)  # revealed: def (cl: type[int]) -> def (str, type[int]) -> int
```

## Structure accepts type forms and preserves their result types

```python
from typing import Annotated, Any, Literal, NewType, Optional, Union

from attrs import define
from typing_extensions import TypeForm, TypeVar, assert_type

from cattrs import BaseConverter, Converter, structure


@define
class Cat:
    lives: int


@define
class Dog:
    name: str


UserId = NewType("UserId", int)
type Pets = list[Cat | Dog]

assert_type(structure({"lives": 9}, Cat | Dog), Cat | Dog)
assert_type(structure("yes", Literal["yes", "no"]), Literal["yes", "no"])
assert_type(structure("1", Annotated[int, "metadata"]), int)
assert_type(structure("1", UserId), UserId)
assert_type(structure([{"lives": 9}], Pets), Pets)
assert_type(structure(None, None), None)
assert_type(structure(1, Any), Any)

base = BaseConverter()
converter = Converter()
assert_type(base.structure("1", int | None), int | None)
assert_type(base.structure({"lives": 9}, Union[Cat, Dog]), Cat | Dog)
assert_type(converter.structure("1", Optional[int]), int | None)
assert_type(converter.structure(["yes"], list[Literal["yes", "no"]]), list[Literal["yes", "no"]])

T = TypeVar("T")


def convert(value: object, target: TypeForm[T]) -> T:
    return converter.structure(value, target)


assert_type(convert("1", int | None), int | None)

bad: str = converter.structure("1", int | None)  # mypy-error: [assignment]
converter.structure("1", 42)  # mypy-error: [arg-type]
```

## Structure hook lookup preserves type forms

```python
from typing import Literal

from typing_extensions import assert_type

from cattrs import Converter, get_structure_hook


converter = Converter()
hook = converter.get_structure_hook(int | None)
assert_type(hook("1", int | None), int | None)
uncached_hook = converter.get_structure_hook(Literal["yes", "no"], cache_result=False)
assert_type(uncached_hook("yes", Literal["yes", "no"]), Literal["yes", "no"])
assert_type(get_structure_hook(int | None)(None, int | None), int | None)
```

## Preconfigured loading APIs accept type forms

```python
from typing import Literal

from typing_extensions import assert_type

from cattrs.preconf.bson import BsonConverter
from cattrs.preconf.cbor2 import Cbor2Converter
from cattrs.preconf.json import JsonConverter
from cattrs.preconf.msgpack import MsgpackConverter
from cattrs.preconf.msgspec import MsgspecJsonConverter
from cattrs.preconf.orjson import OrjsonConverter
from cattrs.preconf.pyyaml import PyyamlConverter
from cattrs.preconf.tomlkit import TomlkitConverter
from cattrs.preconf.tomllib import TomllibConverter
from cattrs.preconf.ujson import UjsonConverter


assert_type(JsonConverter().loads("null", int | None), int | None)
assert_type(UjsonConverter().loads("null", int | None), int | None)
assert_type(OrjsonConverter().loads(b"null", int | None), int | None)
assert_type(MsgspecJsonConverter().loads(b"null", int | None), int | None)
assert_type(MsgpackConverter().loads(b"", int | None), int | None)
assert_type(Cbor2Converter().loads(b"", int | None), int | None)
assert_type(BsonConverter().loads(b"", dict[str, int] | None), dict[str, int] | None)
assert_type(PyyamlConverter().loads("null", int | None), int | None)
assert_type(TomlkitConverter().loads('answer = "yes"', dict[str, Literal["yes", "no"]]), dict[str, Literal["yes", "no"]])
assert_type(TomllibConverter().loads('answer = "yes"', dict[str, Literal["yes", "no"]]), dict[str, Literal["yes", "no"]])

loads_hook = MsgspecJsonConverter().get_loads_hook(int | None)
assert_type(loads_hook(b"null"), int | None)
```
