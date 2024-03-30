# Recipes

This page contains a collection of recipes for custom un-/structuring mechanisms.


## Switching Initializers

When structuring _attrs_ classes, _cattrs_ uses the classes' ``__init__`` method to instantiate objects by default.
In certain situations, you might want to deviate from this behavior and use alternative initializers instead.

For example, consider the following `Point` class describing points in 2D space, which offers two `classmethod`s for alternative creation:

```{doctest} point_group
>>> import math
>>> from attrs import define

>>> @define
... class Point:
...     """A point in 2D space."""
...     x: float
...     y: float
...
...     @classmethod
...     def from_tuple(cls, coordinates: tuple[float, float]) -> "Point":
...         """Create a point from a tuple of Cartesian coordinates."""
...         return Point(*coordinates)
...
...     @classmethod
...     def from_polar(cls, radius: float, angle: float) -> "Point":
...         """Create a point from its polar coordinates."""
...         return Point(radius * math.cos(angle), radius * math.sin(angle))
```


### Selecting an Alternative Initializer

A simple way to _statically_ set one of the `classmethod`s as initializer is to register a structuring hook that holds a reference to the respective callable:

```{doctest} point_group
>>> from inspect import signature
>>> from typing import Callable, TypedDict

>>> from cattrs import Converter
>>> from cattrs.dispatch import StructureHook

>>> def signature_to_typed_dict(fn: Callable) -> type[TypedDict]:
...     """Create a TypedDict reflecting a callable's signature."""
...     params = {p: t.annotation for p, t in signature(fn).parameters.items()}
...     return TypedDict(f"{fn.__name__}_args", params)
...

>>> def make_initializer_from(fn: Callable, conv: Converter) -> StructureHook:
...     """Return a structuring hook from a given callable."""
...     td = signature_to_typed_dict(fn)
...     td_hook = conv.get_structure_hook(td)
...     return lambda v, _: fn(**td_hook(v, td))
```

Now, you can easily structure `Point`s from the specified alternative representation:

```{doctest} point_group
>>> c = Converter()
>>> c.register_structure_hook(Point, make_initializer_from(Point.from_polar, c))

>>> p0 = Point(1.0, 0.0)
>>> p1 = c.structure({"radius": 1.0, "angle": 0.0}, Point)
>>> assert p0 == p1
```


### Dynamically Switching Between Initializers

In some cases, even more flexibility is required and the selection of the initializer must happen at runtime, requiring a dynamic approach.
A typical scenario would be when object structuring happens behind an API and you want to let the user specify which representation of the object they wish to provide in their serialization string.

In such situations, the following hook factory can help you achieve your goal:

```{doctest} point_group
>>> from inspect import signature
>>> from typing import Callable, TypedDict

>>> from cattrs import Converter
>>> from cattrs.dispatch import StructureHook

>>> def signature_to_typed_dict(fn: Callable) -> type[TypedDict]:
...     """Create a TypedDict reflecting a callable's signature."""
...     params = {p: t.annotation for p, t in signature(fn).parameters.items()}
...     return TypedDict(f"{fn.__name__}_args", params)

>>> T = TypeVar("T")
>>> def make_initializer_selection_hook(
...     initializer_key: str,
...     converter: Converter,
... ) -> StructureHook:
...     """Return a structuring hook that dynamically switches between initializers."""
...
...     def select_initializer_hook(specs: dict, cls: type[T]) -> T:
...         """Deserialization with dynamic initializer selection."""
...
...         # If no initializer keyword is specified, use regular __init__
...         if initializer_key not in specs:
...             return converter.structure_attrs_fromdict(specs, cls)
...
...         # Otherwise, call the specified initializer with deserialized arguments
...         specs = specs.copy()
...         initializer_name = specs.pop(initializer_key)
...         initializer = getattr(cls, initializer_name)
...         td = signature_to_typed_dict(initializer)
...         td_hook = converter.get_structure_hook(td)
...         return initializer(**td_hook(specs, td))
...
...     return select_initializer_hook
```

Specifying the key that determines the initializer to be used now lets you dynamically select the `classmethod` as part of the object specification itself:

```{doctest} point_group
>>> c = Converter()
>>> c.register_structure_hook(Point, make_initializer_selection_hook("initializer", c))

>>> p0 = Point(1.0, 0.0)
>>> p1 = c.structure({"initializer": "from_polar", "radius": 1.0, "angle": 0.0}, Point)
>>> p2 = c.structure({"initializer": "from_tuple", "coordinates": (1.0, 0.0)}, Point)
>>> assert p0 == p1 == p2
```
