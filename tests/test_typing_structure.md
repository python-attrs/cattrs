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
