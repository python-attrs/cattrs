# Built-in Hooks

```{currentmodule} cattrs
```

_cattrs_ converters come with with a large repertoire of un/structuring hooks built-in.
As always, complex hooks compose with simpler ones.

## Primitive Values

### `int`, `float`, `str`, `bytes`

When structuring, use any of these types to coerce the object to that type.

```{doctest}

>>> cattrs.structure(1, str)
'1'
>>> cattrs.structure("1", float)
1.0
```

In case the conversion isn't possible the expected exceptions will be propagated out.
The particular exceptions are the same as if you'd tried to do the coercion directly.

```python
>>> cattrs.structure("not-an-int", int)
Traceback (most recent call last):
...
ValueError: invalid literal for int() with base 10: 'not-an-int'
```

Coercion is performed for performance and compatibility reasons.
Any of these hooks can be overriden if pure validation is required instead.

```{doctest}
>>> c = Converter()

>>> @c.register_structure_hook
... def validate(value, type) -> int:
...     if not isinstance(value, type):
...         raise ValueError(f'{value!r} not an instance of {type}')
...     return value

>>> c.structure("1", int)
Traceback (most recent call last):
...
ValueError: '1' not an instance of <class 'int'>
```

When unstructuring, these types are passed through unchanged.

### Enums

Enums are structured by their values, and unstructured to their values.
This works even for complex values, like tuples.

```{doctest}

>>> @unique
... class CatBreed(Enum):
...    SIAMESE = "siamese"
...    MAINE_COON = "maine_coon"
...    SACRED_BIRMAN = "birman"

>>> cattrs.structure("siamese", CatBreed)
<CatBreed.SIAMESE: 'siamese'>

>>> cattrs.unstructure(CatBreed.SIAMESE)
'siamese'
```

Again, in case of errors, the expected exceptions are raised.

### `pathlib.Path`

[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) objects are structured using their string value,
and unstructured into their string value.

```{doctest}
>>> from pathlib import Path

>>> cattrs.structure("/root", Path)
PosixPath('/root')

>>> cattrs.unstructure(Path("/root"))
'/root'
```

In case the conversion isn't possible, the resulting exception is propagated out.

```{versionadded} 23.1.0

```


## Collections and Related Generics


### Optionals

`Optional` primitives and collections are supported out of the box.
[PEP 604](https://peps.python.org/pep-0604/) optionals (`T | None`) are also supported on Python 3.10 and later.

```{doctest}

>>> cattrs.structure(None, int)
Traceback (most recent call last):
...
TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'

>>> print(cattrs.structure(None, int | None))
None
```

Bare `Optional` s (non-parameterized, just `Optional`, as opposed to `Optional[str]`) aren't supported; `Optional[Any]` should be used instead.

`Optionals` handling can be customized using {meth}`register_structure_hook` and {meth}`register_unstructure_hook`.

```{doctest}
>>> converter = Converter()

>>> @converter.register_structure_hook
... def hook(val: Any, type: Any) -> str | None:
...     if val in ("", None):
...         return None
...     return str(val)
...

>>> print(converter.structure("", str | None))
None
```


### Lists

Lists can be structured from any iterable object.
Types converting to lists are:

- `typing.Sequence[T]`
- `typing.MutableSequence[T]`
- `typing.List[T]`
- `list[T]`

In all cases, a new list will be returned, so this operation can be used to copy an iterable into a list.
A bare type, for example `Sequence` instead of `Sequence[int]`, is equivalent to `Sequence[Any]`.

```{doctest}

>>> cattrs.structure((1, 2, 3), MutableSequence[int])
[1, 2, 3]
```

When unstructuring, lists are copied and their contents are handled according to their inner type.
A useful use case for unstructuring collections is to create a deep copy of a complex or recursive collection.

### Dictionaries

Dictionaries can be produced from other mapping objects.
More precisely, the unstructured object must expose an [`items()`](https://docs.python.org/3/library/stdtypes.html#dict.items) method producing an iterable of key-value tuples,
and be able to be passed to the `dict` constructor as an argument.
Types converting to dictionaries are:

- `dict[K, V]` and `typing.Dict[K, V]`
- `collections.abc.MutableMapping[K, V]` and `typing.MutableMapping[K, V]`
- `collections.abc.Mapping[K, V]` and `typing.Mapping[K, V]`

In all cases, a new dict will be returned, so this operation can be used to copy a mapping into a dict.
Any type parameters set to `typing.Any` will be passed through unconverted.
If both type parameters are absent, they will be treated as `Any` too.

```{doctest}

>>> from collections import OrderedDict
>>> cattrs.structure(OrderedDict([(1, 2), (3, 4)]), dict)
{1: 2, 3: 4}
```

Both keys and values are converted.

```{doctest}

>>> cattrs.structure({1: None, 2: 2.0}, dict[str, Optional[int]])
{'1': None, '2': 2}
```

### defaultdicts

[`defaultdicts`](https://docs.python.org/3/library/collections.html#collections.defaultdict)
can be structured by default if they can be initialized using their value type hint.
Supported types are:

- `collections.defaultdict[K, V]`
- `typing.DefaultDict[K, V]`

For example, `defaultdict[str, int]` works since _cattrs_ will initialize it with `defaultdict(int)`.

This also means `defaultdicts` without key and value annotations (bare `defaultdicts`) cannot be structured by default.

`defaultdicts` with arbitrary default factories can be structured by using {meth}`defaultdict_structure_factory <cattrs.cols.defaultdict_structure_factory>`:

```{doctest}
>>> from collections import defaultdict
>>> from cattrs.cols import defaultdict_structure_factory

>>> converter = Converter()
>>> hook = defaultdict_structure_factory(
...     defaultdict[str, int],
...     converter,
...     default_factory=lambda: 1
... )

>>> hook({"key": 1})
defaultdict(<function <lambda> at ...>, {'key': 1})
```

`defaultdicts` are unstructured into plain dictionaries.

```{note}
`defaultdicts` are not supported by the BaseConverter.
```

```{versionadded} 24.2.0

```

### Virtual Subclasses of [`abc.Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) and [`abc.MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

If a class declares itself a virtual subclass of `collections.abc.Mapping` or `collections.abc.MutableMapping` and its initializer accepts a dictionary,
_cattrs_ will be able to structure it by default.

### Homogeneous and Heterogeneous Tuples

Homogeneous and heterogeneous tuples can be structured from iterable objects.
Heterogeneous tuples require an iterable with the number of elements matching the number of type parameters exactly.

Use:

- `Tuple[A, B, C, D]`
- `tuple[A, B, C, D]`

Homogeneous tuples use:

- `Tuple[T, ...]`
- `tuple[T, ...]`

In all cases a tuple will be produced.
Any type parameters set to `typing.Any` will be passed through unconverted.

```{doctest}

>>> cattrs.structure([1, 2, 3], tuple[int, str, float])
(1, '2', 3.0)
```

When unstructuring, heterogeneous tuples unstructure into tuples since it's faster and virtually all serialization libraries support tuples natively.

```{seealso}
[Support for typing.NamedTuple.](#typingnamedtuple)
```

```{note}
Structuring heterogenous tuples are not supported by the BaseConverter.
```

### Deques

Deques can be structured from any iterable object.
Types converting to deques are:

- `typing.Deque[T]`
- `collections.deque[T]`

In all cases, a new **unbounded** deque (`maxlen=None`) will be produced, so this operation can be used to copy an iterable into a deque.
If you want to convert into bounded `deque`, registering a custom structuring hook is a good approach.

```{doctest}

>>> from collections import deque
>>> cattrs.structure((1, 2, 3), deque[int])
deque([1, 2, 3])
```

Deques are unstructured into lists, or into deques when using the {class}`BaseConverter`.

```{versionadded} 23.1.0

```


### Sets and Frozensets

Sets and frozensets can be structured from any iterable object.
Types converting to sets are:

- `typing.Set[T]`
- `typing.MutableSet[T]`
- `set[T]`

Types converting to frozensets are:

- `typing.FrozenSet[T]`
- `frozenset[T]`

In all cases, a new set or frozenset will be returned.
A bare type, for example `MutableSet` instead of `MutableSet[int]`, is equivalent to `MutableSet[Any]`.

```{doctest}

>>> cattrs.structure([1, 2, 3, 4], set)
{1, 2, 3, 4}
```

Sets and frozensets are unstructured into the same class.


### Typed Dicts

[TypedDicts](https://peps.python.org/pep-0589/) can be structured from mapping objects, usually dictionaries.

```{doctest}
>>> from typing import TypedDict

>>> class MyTypedDict(TypedDict):
...    a: int

>>> cattrs.structure({"a": "1"}, MyTypedDict)
{'a': 1}
```

Both [_total_ and _non-total_](https://peps.python.org/pep-0589/#totality) TypedDicts are supported, and inheritance between any combination works.
Generic TypedDicts work on Python 3.11 and later, since that is the first Python version that supports them in general.

[`typing.Required` and `typing.NotRequired`](https://peps.python.org/pep-0655/) are supported.

:::{caution}
If `from __future__ import annotations` is used or if annotations are given as strings, `Required` and `NotRequired` are ignored by cattrs.
See [note in the Python documentation](https://docs.python.org/3/library/typing.html#typing.TypedDict.__optional_keys__).
:::

[Similar to _attrs_ classes](customizing.md#using-cattrsgen-hook-factories), un/structuring can be customized using {meth}`cattrs.gen.typeddicts.make_dict_structure_fn` and {meth}`cattrs.gen.typeddicts.make_dict_unstructure_fn`.

```{doctest}
>>> from typing import TypedDict
>>> from cattrs import Converter
>>> from cattrs.gen import override
>>> from cattrs.gen.typeddicts import make_dict_structure_fn

>>> class MyTypedDict(TypedDict):
...     a: int
...     b: int

>>> c = Converter()
>>> c.register_structure_hook(
...     MyTypedDict,
...     make_dict_structure_fn(
...         MyTypedDict,
...         c,
...         a=override(rename="a-with-dash")
...     )
... )

>>> c.structure({"a-with-dash": 1, "b": 2}, MyTypedDict)
{'b': 2, 'a': 1}
```

TypedDicts unstructure into dictionaries, potentially unchanged (depending on the exact field types and registered hooks).

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

```{versionadded} 23.1.0

```


## _attrs_ Classes and Dataclasses

_attrs_ classes and dataclasses work out of the box.
The fields require type annotations (even if static type-checking is not being used), or they will be treated as [](#typingany).

When structuring, given a mapping `d` and class `A`, _cattrs_ will instantiate `A` with `d` unpacked.

```{doctest}

>>> @define
... class A:
...     a: int
...     b: int

>>> cattrs.structure({'a': 1, 'b': '2'}, A)
A(a=1, b=2)
```

Tuples can be structured into classes using {meth}`structure_attrs_fromtuple() <cattrs.structure_attrs_fromtuple>` (`fromtuple` as in the opposite of [`attrs.astuple`](https://www.attrs.org/en/stable/api.html#attrs.astuple) and {meth}`BaseConverter.unstructure_attrs_astuple`).

```{doctest}

>>> @define
... class A:
...     a: str
...     b: int

>>> cattrs.structure_attrs_fromtuple(['string', '2'], A)
A(a='string', b=2)
```

Loading from tuples can be made the default by creating a new {class}`Converter <cattrs.Converter>` with `unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE`.

```{doctest}

>>> converter = cattrs.Converter(unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE)
>>> @define
... class A:
...     a: str
...     b: int

>>> converter.structure(['string', '2'], A)
A(a='string', b=2)
```

Structuring from tuples can also be made the default for specific classes only by registering a hook the usual way.

```{doctest}

>>> converter = cattrs.Converter()

>>> @define
... class A:
...     a: str
...     b: int

>>> converter.register_structure_hook(A, converter.structure_attrs_fromtuple)
```


### Generics

Generic _attrs_ classes and dataclasses are fully supported, both using `typing.Generic` and [PEP 695](https://peps.python.org/pep-0695/).

```python
>>> @define
... class A[T]:
...    a: T

>>> cattrs.structure({"a": "1"}, A[int])
A(a=1)
```


### Using Attribute Types and Converters

By default, {meth}`structure() <cattrs.BaseConverter.structure>` will use hooks registered using {meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>`
to convert values to the attribute type, and proceed to invoking any converters registered on attributes with `field`.

```{doctest}

>>> from ipaddress import IPv4Address, ip_address
>>> converter = cattrs.Converter()

# Note: register_structure_hook has not been called, so this will fallback to 'ip_address'
>>> @define
... class A:
...     a: IPv4Address = field(converter=ip_address)

>>> converter.structure({'a': '127.0.0.1'}, A)
A(a=IPv4Address('127.0.0.1'))
```

Priority is still given to hooks registered with {meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>`,
but this priority can be inverted by setting `prefer_attrib_converters` to `True`.

```{doctest}

>>> converter = cattrs.Converter(prefer_attrib_converters=True)

>>> @define
... class A:
...     a: int = field(converter=lambda v: int(v) + 5)

>>> converter.structure({'a': '10'}, A)
A(a=15)
```

```{seealso}
If an _attrs_ or dataclass class uses inheritance and as such has one or several subclasses, it can be structured automatically to its exact subtype by using the [include subclasses](strategies.md#include-subclasses-strategy) strategy.
```


## Unions

Unions of `NoneType` and a single other type (also known as optionals) are supported by a [special case](#optionals).


### Automatic Disambiguation

_cattrs_ includes an opinionated strategy for automatically handling unions of _attrs_ classes; see [](unions.md#default-union-strategy) for details.

When unstructuring these kinds of unions, each union member will be unstructured according to the hook for that type.


### Unions of Simple Types

_cattrs_ comes with the [](strategies.md#union-passthrough), which enables converters to structure unions of many primitive types and literals.
This strategy can be applied to any converter, and is pre-applied to all [preconf](preconf.md) converters according to their underlying protocols.


## Special Typing Forms


### `typing.Any`

When structuring, use `typing.Any` to avoid applying any conversions to the object you're structuring; it will simply be passed through.

```{doctest}

>>> cattrs.structure(1, Any)
1
>>> d = {1: 1}
>>> cattrs.structure(d, Any) is d
True
```

When unstructuring, `typing.Any` will make the value be unstructured according to its runtime class.

```{versionchanged} 24.1.0
Previously, the unstructuring rules for `Any` were underspecified, leading to inconsistent behavior.
```

```{versionchanged} 24.1.0
`typing_extensions.Any` is now also supported.
```

### `typing.Literal`

When structuring, [PEP 586](https://peps.python.org/pep-0586/) literals are validated to be in the allowed set of values.

```{doctest}
>>> from typing import Literal

>>> cattrs.structure(1, Literal[1, 2])
1
```

When unstructuring, literals are passed through.

```{versionadded} 1.7.0

```

### `typing.NamedTuple`

Named tuples with type hints (created from [`typing.NamedTuple`](https://docs.python.org/3/library/typing.html#typing.NamedTuple)) are supported.
Named tuples are un/structured using tuples or lists by default.

The {mod}`cattrs.cols` module contains hook factories for un/structuring named tuples using dictionaries instead,
[see here for details](customizing.md#customizing-named-tuples).

```{versionadded} 24.1.0

```

### `typing.Final`

[PEP 591](https://peps.python.org/pep-0591/) Final attribute types (`Final[int]`) are supported and handled according to the inner type (in this case, `int`).

```{versionadded} 23.1.0

```


### `typing.Annotated`

[PEP 593](https://www.python.org/dev/peps/pep-0593/) annotations (`typing.Annotated[type, ...]`) are supported and are handled using the first type present in the annotated type.

```{versionadded} 1.4.0

```


### Type Aliases

[Type aliases](https://docs.python.org/3/library/typing.html#type-aliases) are supported on Python 3.12+ and are handled according to the rules for their underlying type.
Their hooks can also be overriden using [](customizing.md#predicate-hooks).

```{warning}
Type aliases using [`typing.TypeAlias`](https://docs.python.org/3/library/typing.html#typing.TypeAlias) aren't supported since there is no way at runtime to distinguish them from their underlying types.
```

```python
>>> from datetime import datetime, UTC

>>> type IsoDate = datetime

>>> converter = cattrs.Converter()
>>> converter.register_structure_hook_func(
...     lambda t: t is IsoDate, lambda v, _: datetime.fromisoformat(v)
... )
>>> converter.register_unstructure_hook_func(
...     lambda t: t is IsoDate, lambda v: v.isoformat()
... )

>>> converter.structure("2022-01-01", IsoDate)
datetime.datetime(2022, 1, 1, 0, 0)
>>> converter.unstructure(datetime.now(UTC), unstructure_as=IsoDate)
'2023-11-20T23:10:46.728394+00:00'
```

```{versionadded} 24.1.0

```


### `typing.NewType`

[NewTypes](https://docs.python.org/3/library/typing.html#newtype) are supported and are handled according to the rules for their underlying type.
Their hooks can also be overriden using {meth}`Converter.register_structure_hook() <cattrs.BaseConverter.register_structure_hook>`.

```{doctest}

>>> from typing import NewType
>>> from datetime import datetime

>>> IsoDate = NewType("IsoDate", datetime)

>>> converter = cattrs.Converter()
>>> converter.register_structure_hook(IsoDate, lambda v, _: datetime.fromisoformat(v))

>>> converter.structure("2022-01-01", IsoDate)
datetime.datetime(2022, 1, 1, 0, 0)
```

```{versionadded} 22.2.0

```


### `typing.Protocol`

[Protocols](https://peps.python.org/pep-0544/) cannot be structured by default and so require custom hooks.

Protocols are unstructured according to the actual runtime type of the value.

```{versionadded} 1.9.0

```

### `typing.Self`

Attributes annotated using [the Self type](https://docs.python.org/3/library/typing.html#typing.Self) are supported in _attrs_ classes, dataclasses, TypedDicts and NamedTuples
(when using [the dict un/structure factories](customizing.md#customizing-named-tuples)).

```{doctest}
>>> from typing import Self

>>> @define
... class LinkedListNode:
...     element: int
...     next: Self | None = None

>>> cattrs.unstructure(LinkedListNode(1, LinkedListNode(2, None)))
{'element': 1, 'next': {'element': 2, 'next': None}}
>>> cattrs.structure({'element': 1, 'next': {'element': 2, 'next': None}}, LinkedListNode)
LinkedListNode(element=1, next=LinkedListNode(element=2, next=None))
```

```{note}
Attributes annotated with `typing.Self` are not supported by the BaseConverter, as this is too complex for it.
```

```{versionadded} 25.1.0

```
