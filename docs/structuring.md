# What You Can Structure and How

The philosophy of _cattrs_ structuring is simple: give it an instance of Python
built-in types and collections, and a type describing the data you want out.
_cattrs_ will convert the input data into the type you want, or throw an
exception.

All structuring conversions are composable, where applicable. This is
demonstrated further in the examples.

## Primitive Values

### `typing.Any`

Use `typing.Any` to avoid applying any conversions to the object you're
structuring; it will simply be passed through.

```{doctest}

>>> cattrs.structure(1, Any)
1
>>> d = {1: 1}
>>> cattrs.structure(d, Any) is d
True
```

### `int`, `float`, `str`, `bytes`

Use any of these primitive types to convert the object to the type.

```{doctest}

>>> cattrs.structure(1, str)
'1'
>>> cattrs.structure("1", float)
1.0
```

In case the conversion isn't possible, the expected exceptions will be
propagated out. The particular exceptions are the same as if you'd tried to
do the conversion yourself, directly.

```python
>>> cattrs.structure("not-an-int", int)
Traceback (most recent call last):
...
ValueError: invalid literal for int() with base 10: 'not-an-int'
```

### Enums

Enums will be structured by their values. This works even for complex values,
like tuples.

```{doctest}

>>> @unique
... class CatBreed(Enum):
...    SIAMESE = "siamese"
...    MAINE_COON = "maine_coon"
...    SACRED_BIRMAN = "birman"

>>> cattrs.structure("siamese", CatBreed)
<CatBreed.SIAMESE: 'siamese'>
```

Again, in case of errors, the expected exceptions will fly out.

```python
>>> cattrs.structure("alsatian", CatBreed)
Traceback (most recent call last):
...
ValueError: 'alsatian' is not a valid CatBreed
```

### `pathlib.Path`

[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) objects are structured using their string value.

```{doctest}
>>> from pathlib import Path

>>> cattrs.structure("/root", Path)
PosixPath('/root')
```

In case the conversion isn't possible, the resulting exception is propagated out.

```{versionadded} 23.1.0

```

## Collections and Other Generics

### Optionals

`Optional` primitives and collections are supported out of the box.

```{doctest}

>>> cattrs.structure(None, int)
Traceback (most recent call last):
...
TypeError: int() argument must be a string, a bytes-like object or a number, not 'NoneType'
>>> cattrs.structure(None, Optional[int])
>>> # None was returned.
```

Bare `Optional` s (non-parameterized, just `Optional`, as opposed to
`Optional[str]`) aren't supported, use `Optional[Any]` instead.

The Python 3.10 more readable syntax, `str | None` instead of `Optional[str]`, is also supported.

This generic type is composable with all other converters.

```{doctest}

>>> cattrs.structure(1, Optional[float])
1.0
```

### Lists

Lists can be produced from any iterable object. Types converting to lists are:

- `Sequence[T]`
- `MutableSequence[T]`
- `List[T]`
- `list[T]`

In all cases, a new list will be returned, so this operation can be used to
copy an iterable into a list. A bare type, for example `Sequence` instead of
`Sequence[int]`, is equivalent to `Sequence[Any]`.

```{doctest}

>>> cattrs.structure((1, 2, 3), MutableSequence[int])
[1, 2, 3]
```

These generic types are composable with all other converters.

```{doctest}

>>> cattrs.structure((1, None, 3), list[Optional[str]])
['1', None, '3']
```

### Deques

Deques can be produced from any iterable object. Types converting
to deques are:

- `Deque[T]`
- `deque[T]`

In all cases, a new **unbounded** deque (`maxlen=None`) will be returned,
so this operation can be used to copy an iterable into a deque.
If you want to convert into bounded `deque`, registering a custom structuring hook is a good approach.

```{doctest}

>>> from collections import deque
>>> cattrs.structure((1, 2, 3), deque[int])
deque([1, 2, 3])
```

These generic types are composable with all other converters.

```{doctest}
>>> cattrs.structure((1, None, 3), deque[Optional[str]])
deque(['1', None, '3'])
```

```{versionadded} 23.1.0

```

### Sets and Frozensets

Sets and frozensets can be produced from any iterable object. Types converting
to sets are:

- `Set[T]`
- `MutableSet[T]`
- `set[T]`

Types converting to frozensets are:

- `FrozenSet[T]`
- `frozenset[T]`

In all cases, a new set or frozenset will be returned, so this operation can be
used to copy an iterable into a set. A bare type, for example `MutableSet`
instead of `MutableSet[int]`, is equivalent to `MutableSet[Any]`.

```{doctest}

>>> cattrs.structure([1, 2, 3, 4], Set)
{1, 2, 3, 4}
```

These generic types are composable with all other converters.

```{doctest}

>>> cattrs.structure([[1, 2], [3, 4]], set[frozenset[str]])
{frozenset({'2', '1'}), frozenset({'4', '3'})}
```

### Dictionaries

Dicts can be produced from other mapping objects. To be more precise, the
object being converted must expose an `items()` method producing an iterable
key-value tuples, and be able to be passed to the `dict` constructor as an
argument. Types converting to dictionaries are:

- `Dict[K, V]`
- `MutableMapping[K, V]`
- `Mapping[K, V]`
- `dict[K, V]`

In all cases, a new dict will be returned, so this operation can be
used to copy a mapping into a dict. Any type parameters set to `typing.Any`
will be passed through unconverted. If both type parameters are absent,
they will be treated as `Any` too.

```{doctest}

>>> from collections import OrderedDict
>>> cattrs.structure(OrderedDict([(1, 2), (3, 4)]), Dict)
{1: 2, 3: 4}
```

These generic types are composable with all other converters. Note both keys
and values can be converted.

```{doctest}

>>> cattrs.structure({1: None, 2: 2.0}, dict[str, Optional[int]])
{'1': None, '2': 2}
```

### Typed Dicts

[TypedDicts](https://peps.python.org/pep-0589/) can be produced from mapping objects, usually dictionaries.

```{doctest}
>>> from typing import TypedDict

>>> class MyTypedDict(TypedDict):
...    a: int

>>> cattrs.structure({"a": "1"}, MyTypedDict)
{'a': 1}
```

Both [_total_ and _non-total_](https://peps.python.org/pep-0589/#totality) TypedDicts are supported, and inheritance between any combination works (except on 3.8 when `typing.TypedDict` is used, see below).
Generic TypedDicts work on Python 3.11 and later, since that is the first Python version that supports them in general.

[`typing.Required` and `typing.NotRequired`](https://peps.python.org/pep-0655/) are supported.

On Python 3.8, using `typing_extensions.TypedDict` is recommended since `typing.TypedDict` doesn't support all necessary features, so certain combinations of subclassing, totality and `typing.Required` won't work.

[Similar to _attrs_ classes](customizing.md#using-cattrsgen-generators), structuring can be customized using {meth}`cattrs.gen.typeddicts.make_dict_structure_fn`.

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

```{seealso} [Unstructuring TypedDicts.](unstructuring.md#typed-dicts)

```

```{versionadded} 23.1.0

```

### Homogeneous and Heterogeneous Tuples

Homogeneous and heterogeneous tuples can be produced from iterable objects.
Heterogeneous tuples require an iterable with the number of elements matching
the number of type parameters exactly. Use:

- `Tuple[A, B, C, D]`
- `tuple[A, B, C, D]`

Homogeneous tuples use:

- `Tuple[T, ...]`
- `tuple[T, ...]`

In all cases a tuple will be returned. Any type parameters set to
`typing.Any` will be passed through unconverted.

```{doctest}

>>> cattrs.structure([1, 2, 3], tuple[int, str, float])
(1, '2', 3.0)
```

The tuple conversion is composable with all other converters.

```{doctest}

>>> cattrs.structure([{1: 1}, {2: 2}], tuple[dict[str, float], ...])
({'1': 1.0}, {'2': 2.0})
```

### Unions

Unions of `NoneType` and a single other type are supported (also known as
`Optional` s). All other unions require a disambiguation function.

#### Automatic Disambiguation

In the case of a union consisting exclusively of `attrs` classes, `cattrs`
will attempt to generate a disambiguation function automatically; this will
succeed only if each class has a unique field. Given the following classes:

```python
>>> @define
... class A:
...     a = field()
...     x = field()

>>> @define
... class B:
...     a = field()
...     y = field()

>>> @define
... class C:
...     a = field()
...     z = field()
```

`cattrs` can deduce only instances of `A` will contain `x`, only instances
of `B` will contain `y`, etc. A disambiguation function using this
information will then be generated and cached. This will happen automatically,
the first time an appropriate union is structured.

#### Manual Disambiguation

To support arbitrary unions, register a custom structuring hook for the union
(see [Registering custom structuring hooks](structuring.md#registering-custom-structuring-hooks)).

Another option is to use a custom tagged union strategy (see [Strategies - Tagged Unions](strategies.md#tagged-unions-strategy)).

### `typing.Final`

[PEP 591](https://peps.python.org/pep-0591/) Final attribute types (`Final[int]`) are supported and structured appropriately.

```{versionadded} 23.1.0

```

```{seealso} [Unstructuring Final.](unstructuring.md#typingfinal)

```

### `typing.Annotated`

[PEP 593](https://www.python.org/dev/peps/pep-0593/) annotations (`typing.Annotated[type, ...]`) are supported and are
matched using the first type present in the annotated type.

## `typing.NewType`

[NewTypes](https://docs.python.org/3/library/typing.html#newtype) are supported and are structured according to the rules for their underlying type.
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

```{seealso} [Unstructuring NewTypes.](unstructuring.md#typingnewtype)

```

```{note}
NewTypes are not supported by the legacy BaseConverter.
```

## _attrs_ Classes and Dataclasses

### Simple _attrs_ Classes and Dataclasses

_attrs_ classes and dataclasses using primitives, collections of primitives
and their own converters work out of the box. Given a mapping `d` and class
`A`, _cattrs_ will simply instantiate `A` with `d` unpacked.

```{doctest}

>>> @define
... class A:
...     a: int
...     b: int

>>> cattrs.structure({'a': 1, 'b': '2'}, A)
A(a=1, b=2)
```

Classes like these deconstructed into tuples can be structured using
{meth}`structure_attrs_fromtuple() <cattrs.structure_attrs_fromtuple>` (`fromtuple` as in the opposite of
`attr.astuple` and `converter.unstructure_attrs_astuple`).

```{doctest}

>>> @define
... class A:
...     a: str
...     b: int

>>> cattrs.structure_attrs_fromtuple(['string', '2'], A)
A(a='string', b=2)
```

Loading from tuples can be made the default by creating a new {class}`Converter <cattrs.Converter>` with
`unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE`.

```{doctest}

>>> converter = cattrs.Converter(unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE)
>>> @define
... class A:
...     a: str
...     b: int

>>> converter.structure(['string', '2'], A)
A(a='string', b=2)
```

Structuring from tuples can also be made the default for specific classes only;
see registering custom structure hooks below.

## Using Attribute Types and Converters

By default, {meth}`structure() <cattrs.BaseConverter.structure>` will use hooks registered using {meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>`,
to convert values to the attribute type, and fallback to invoking any converters registered on
attributes with `attrib`.

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

>>> converter.register_structure_hook(int, lambda v, t: int(v))

>>> @define
... class A:
...     a: int = field(converter=lambda v: int(v) + 5)

>>> converter.structure({'a': '10'}, A)
A(a=15)
```

### Complex `attrs` Classes and Dataclasses

Complex `attrs` classes and dataclasses are classes with type information
available for some or all attributes. These classes support almost arbitrary
nesting.

Type information is supported by attrs directly, and can be set using type
annotations when using Python 3.6+, or by passing the appropriate type to
`attr.ib`.

```{doctest}

>>> @define
... class A:
...     a: int

>>> attr.fields(A).a
Attribute(name='a', default=NOTHING, validator=None, repr=True, eq=True, eq_key=None, order=True, order_key=None, hash=None, init=True, metadata=mappingproxy({}), type=<class 'int'>, converter=None, kw_only=False, inherited=False, on_setattr=None, alias='a')
```

Type information, when provided, can be used for all attribute types, not only
attributes holding `attrs` classes and dataclasses.

```{doctest}

>>> @define
... class A:
...     a: int = 0

>>> @define
... class B:
...     b: A

>>> cattrs.structure({'b': {'a': '1'}}, B)
B(b=A(a=1))
```

Finally, if an `attrs` or `dataclass` class uses inheritance and as such has one or several subclasses, it can be structured automatically to its exact subtype by using the [include subclasses](strategies.md#include-subclasses-strategy) strategy.

## Registering Custom Structuring Hooks

_cattrs_ doesn't know how to structure non-_attrs_ classes by default,
so it has to be taught. This can be done by registering structuring hooks on
a converter instance (including the global converter).

Here's an example involving a simple, classic (i.e. non-_attrs_) Python class.

```{doctest}

>>> class C:
...     def __init__(self, a):
...         self.a = a
...     def __repr__(self):
...         return f'C(a={self.a})'

>>> cattrs.structure({'a': 1}, C)
Traceback (most recent call last):
...
StructureHandlerNotFoundError: Unsupported type: <class '__main__.C'>. Register a structure hook for it.

>>> cattrs.register_structure_hook(C, lambda d, t: C(**d))
>>> cattrs.structure({'a': 1}, C)
C(a=1)
```

The structuring hooks are callables that take two arguments: the object to
convert to the desired class and the type to convert to.
(The type may seem redundant but is useful when dealing with generic types.)

When using {meth}`cattrs.register_structure_hook`, the hook will be registered on the global converter.
If you want to avoid changing the global converter, create an instance of {class}`cattrs.Converter` and register the hook on that.

In some situations, it is not possible to decide on the converter using typing mechanisms alone (such as with _attrs_ classes). In these situations,
_cattrs_ provides a {meth}`register_unstructure_hook_func() <cattrs.BaseConverter.register_unstructure_hook_func()>` hook instead, which accepts a predicate function to determine whether that type can be handled instead.

The function-based hooks are evaluated after the class-based hooks. In the case where both a class-based hook and a function-based hook are present, the class-based hook will be used.

```{doctest}

>>> class D:
...     custom = True
...     def __init__(self, a):
...         self.a = a
...     def __repr__(self):
...         return f'D(a={self.a})'
...     @classmethod
...     def deserialize(cls, data):
...         return cls(data["a"])

>>> cattrs.register_structure_hook_func(
...     lambda cls: getattr(cls, "custom", False), lambda d, t: t.deserialize(d)
... )

>>> cattrs.structure({'a': 2}, D)
D(a=2)
```

## Structuring Hook Factories

Hook factories operate one level higher than structuring hooks; structuring
hooks are functions registered to a class or predicate, and hook factories
are functions (registered via a predicate) that produce structuring hooks.

Structuring hooks factories are registered using {meth}`Converter.register_structure_hook_factory() <cattrs.BaseConverter.register_structure_hook_factory>`.

Here's a small example showing how to use factory hooks to apply the `forbid_extra_keys` to all attrs classes:

```{doctest}

>>> from attrs import define, has
>>> from cattrs.gen import make_dict_structure_fn

>>> c = cattrs.Converter()
>>> c.register_structure_hook_factory(
...     has,
...     lambda cl: make_dict_structure_fn(
...         cl, c, _cattrs_forbid_extra_keys=True, _cattrs_detailed_validation=False
...     )
... )

>>> @define
... class E:
...    an_int: int

>>> c.structure({"an_int": 1, "else": 2}, E)
Traceback (most recent call last):
...
cattrs.errors.ForbiddenExtraKeysError: Extra fields in constructor for E: else
```

A complex use case for hook factories is described over at {ref}`usage:Using factory hooks`.
