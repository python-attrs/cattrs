# What You Can Unstructure and How

Unstructuring is intended to convert high-level, structured Python data (like
instances of complex classes) into simple, unstructured data (like
dictionaries).

Unstructuring is simpler than structuring in that no target types are required.
Simply provide an argument to {meth}`Converter.unstructure() <cattrs.BaseConverter.unstructure>` and _cattrs_ will produce a
result based on the registered unstructuring hooks.
A number of default unstructuring hooks are documented here.

## Primitive Types and Collections

Primitive types (integers, floats, strings...) are simply passed through.
Collections are copied. There's relatively little value in unstructuring
these types directly as they are already unstructured and third-party
libraries tend to support them directly.

A useful use case for unstructuring collections is to create a deep copy of
a complex or recursive collection.

```{doctest}

>>> # A dictionary of strings to lists of tuples of floats.
>>> data = {'a': [[1.0, 2.0], [3.0, 4.0]]}

>>> copy = cattrs.unstructure(data)
>>> data == copy
True
>>> data is copy
False
```

### Typed Dicts

[TypedDicts](https://peps.python.org/pep-0589/) unstructure into dictionaries, potentially unchanged (depending on the exact field types and registered hooks).

```{doctest}
>>> from typing import TypedDict
>>> from datetime import datetime, timezone
>>> from cattrs import Converter

>>> class MyTypedDict(TypedDict):
...    a: datetime

>>> c = Converter()
>>> c.register_unstructure_hook(datetime, lambda d: d.timestamp())

>>> c.unstructure({"a": datetime(1970, 1, 1, tzinfo=timezone.utc)}, unstructure_as=MyTypedDict)
{'a': 0.0}
```

Generic TypedDicts work on Python 3.11 and later, since that is the first Python version that supports them in general.

On Python 3.8, using `typing_extensions.TypedDict` is recommended since `typing.TypedDict` doesn't support all necessary features, so certain combinations of subclassing, totality and `typing.Required` won't work.

[Similar to _attrs_ classes](customizing.md#using-cattrsgen-generators), unstructuring can be customized using {meth}`cattrs.gen.typeddicts.make_dict_unstructure_fn`.

```{doctest}
>>> from typing import TypedDict
>>> from cattrs import Converter
>>> from cattrs.gen import override
>>> from cattrs.gen.typeddicts import make_dict_unstructure_fn

>>> class MyTypedDict(TypedDict):
...     a: int
...     b: int

>>> c = Converter()
>>> c.register_unstructure_hook(
...     MyTypedDict,
...     make_dict_unstructure_fn(
...         MyTypedDict,
...         c,
...         a=override(omit=True)
...     )
... )

>>> c.unstructure({"a": 1, "b": 2}, unstructure_as=MyTypedDict)
{'b': 2}
```

```{seealso} [Structuring TypedDicts.](structuring.md#typed-dicts)

```

```{versionadded} 23.1.0

```

## `pathlib.Path`

[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) objects are unstructured into their string value.

```{doctest}
>>> from pathlib import Path

>>> cattrs.unstructure(Path("/root"))
'/root'
```

```{versionadded} 23.1.0

```

## Customizing Collection Unstructuring

```{important}
This feature is supported for Python 3.9 and later.
```

Sometimes it's useful to be able to override collection unstructuring in a
generic way. A common example is using a JSON library that doesn't support
sets, but expects lists and tuples instead.

Using ordinary unstructuring hooks for this is unwieldy due to the semantics of
[singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch);
in other words, you'd need to register hooks for all specific types of set you're using (`set[int]`, `set[float]`,
`set[str]`...), which is not useful.

Function-based hooks can be used instead, but come with their own set of
challenges - they're complicated to write efficiently.

The {class}`Converter <cattrs.Converter>` supports easy customizations of collection unstructuring
using its `unstruct_collection_overrides` parameter. For example, to
unstructure all sets into lists, try the following:

```{doctest}

>>> from collections.abc import Set
>>> converter = cattrs.Converter(unstruct_collection_overrides={Set: list})

>>> converter.unstructure({1, 2, 3})
[1, 2, 3]
```

Going even further, the Converter contains heuristics to support the
following Python types, in order of decreasing generality:

- `Sequence`, `MutableSequence`, `list`, `deque`, `tuple`
- `Set`, `frozenset`, `MutableSet`, `set`
- `Mapping`, `MutableMapping`, `dict`, `defaultdict`, `OrderedDict`, `Counter`

For example, if you override the unstructure type for `Sequence`, but not for
`MutableSequence`, `list` or `tuple`, the override will also affect those
types. An easy way to remember the rule:

- all `MutableSequence` s are `Sequence` s, so the override will apply
- all `list` s are `MutableSequence` s, so the override will apply
- all `tuple` s are `Sequence` s, so the override will apply

If, however, you override only `MutableSequence`, fields annotated as
`Sequence` will not be affected (since not all sequences are mutable
sequences), and fields annotated as tuples will not be affected (since tuples
are not mutable sequences in the first place).

Similar logic applies to the set and mapping hierarchies.

Make sure you're using the types from `collections.abc` on Python 3.9+, and
from `typing` on older Python versions.

### `typing.Final`

[PEP 591](https://peps.python.org/pep-0591/) Final attribute types (`Final[int]`) are supported and unstructured appropriately.

```{versionadded} 23.1.0

```

```{seealso} [Structuring Final.](structuring.md#typingfinal)

```

## `typing.Annotated`

Fields marked as `typing.Annotated[type, ...]` are supported and are matched
using the first type present in the annotated type.

## `typing.NewType`

[NewTypes](https://docs.python.org/3/library/typing.html#newtype) are supported and are unstructured according to the rules for their underlying type.
Their hooks can also be overriden using {meth}`Converter.register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>`.

```{versionadded} 22.2.0

```

```{seealso} [Structuring NewTypes.](structuring.md#typingnewtype)

```

```{note}
NewTypes are not supported by the legacy {class}`BaseConverter <cattrs.BaseConverter>`.
```

## _attrs_ Classes and Dataclasses

_attrs_ classes and dataclasses are supported out of the box.
{class}`cattrs.Converters <cattrs.Converter>` support two unstructuring strategies:

- `UnstructureStrategy.AS_DICT` - similar to [`attrs.asdict()`](https://www.attrs.org/en/stable/api.html#attrs.asdict), unstructures _attrs_ and dataclass instances into dictionaries. This is the default.
- `UnstructureStrategy.AS_TUPLE` - similar to [`attrs.astuple()`](https://www.attrs.org/en/stable/api.html#attrs.astuple), unstructures _attrs_ and dataclass instances into tuples.

```{doctest}

>>> @define
... class C:
...     a = field()
...     b = field()

>>> inst = C(1, 'a')

>>> converter = cattrs.Converter(unstruct_strat=cattrs.UnstructureStrategy.AS_TUPLE)

>>> converter.unstructure(inst)
(1, 'a')
```

## Mixing and Matching Strategies

Converters publicly expose two helper methods, {meth}`Converter.unstructure_attrs_asdict() <cattrs.BaseConverter.unstructure_attrs_asdict>`
and {meth}`Converter.unstructure_attrs_astuple() <cattrs.BaseConverter.unstructure_attrs_astuple>`.
These methods can be used with custom unstructuring hooks to selectively apply one strategy to instances of particular classes.

Assume two nested _attrs_ classes, `Inner` and `Outer`; instances of `Outer` contain instances of `Inner`.
Instances of `Outer` should be unstructured as dictionaries, and instances of `Inner` as tuples.
Here's how to do this.

```{doctest}

>>> @define
... class Inner:
...     a: int

>>> @define
... class Outer:
...     i: Inner

>>> inst = Outer(i=Inner(a=1))

>>> converter = cattrs.Converter()
>>> converter.register_unstructure_hook(Inner, converter.unstructure_attrs_astuple)

>>> converter.unstructure(inst)
{'i': (1,)}
```

Of course, these methods can be used directly as well, without changing the converter strategy.

```{doctest}

>>> @define
... class C:
...     a: int
...     b: str

>>> inst = C(1, 'a')

>>> converter = cattrs.Converter()

>>> converter.unstructure_attrs_astuple(inst)  # Default is AS_DICT.
(1, 'a')
```

## Unstructuring Hook Factories

Hook factories operate one level higher than unstructuring hooks; unstructuring
hooks are functions registered to a class or predicate, and hook factories
are functions (registered via a predicate) that produce unstructuring hooks.

Unstructuring hooks factories are registered using {meth}`Converter.register_unstructure_hook_factory() <cattrs.BaseConverter.register_unstructure_hook_factory>`.

Here's a small example showing how to use factory hooks to skip unstructuring `init=False` attributes on all _attrs_ classes.

```{doctest}

>>> from attrs import define, has, field, fields
>>> from cattrs import override
>>> from cattrs.gen import make_dict_unstructure_fn

>>> c = cattrs.Converter()
>>> c.register_unstructure_hook_factory(
...     has,
...     lambda cl: make_dict_unstructure_fn(
...         cl, c, **{a.name: override(omit=True) for a in fields(cl) if not a.init}
...     )
... )

>>> @define
... class E:
...    an_int: int
...    another_int: int = field(init=False)

>>> inst = E(1)
>>> inst.another_int = 5
>>> c.unstructure(inst)
{'an_int': 1}
```

A complex use case for hook factories is described over at {ref}`usage:Using factory hooks`.
