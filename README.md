# *cattrs*: Flexible Object Serialization and Validation

*Because validation belongs to the edges.*

[![Documentation](https://img.shields.io/badge/Docs-Read%20The%20Docs-black)](https://catt.rs/)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cattrs.svg)](https://pypi.python.org/pypi/cattrs)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/cattrs.svg)](https://github.com/python-attrs/cattrs)
[![Downloads](https://static.pepy.tech/badge/cattrs/month)](https://pepy.tech/project/cattrs)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Tinche/22405310d6a663164d894a2beab4d44d/raw/covbadge.json)](https://github.com/python-attrs/cattrs/actions/workflows/main.yml)

---

<!-- begin-teaser -->

**cattrs** is a Swiss Army knife for (un)structuring and validating data in Python.
In practice, that means it converts **unstructured dictionaries** into **proper classes** and back, while **validating** their contents.

<!-- end-teaser -->


## Example

<!-- begin-example -->

_cattrs_ works best with [_attrs_](https://www.attrs.org/) classes, and [dataclasses](https://docs.python.org/3/library/dataclasses.html) where simple (un-)structuring works out of the box, even for nested data, without polluting your data model with serialization details:

```python
>>> from attrs import define
>>> from cattrs import structure, unstructure
>>> @define
... class C:
...     a: int
...     b: list[str]
>>> instance = structure({'a': 1, 'b': ['x', 'y']}, C)
>>> instance
C(a=1, b=['x', 'y'])
>>> unstructure(instance)
{'a': 1, 'b': ['x', 'y']}
```

<!-- end-teaser -->
<!-- end-example -->

Have a look at [*Why *cattrs*?*](https://catt.rs/en/latest/why.html) for more examples!

<!-- begin-why -->

## Features

### Recursive Unstructuring

- _attrs_ classes and dataclasses are converted into dictionaries in a way similar to `attrs.asdict()`, or into tuples in a way similar to `attrs.astuple()`.
- Enumeration instances are converted to their values.
- Other types are let through without conversion. This includes types such as integers, dictionaries, lists and instances of non-_attrs_ classes.
- Custom converters for any type can be registered using `register_unstructure_hook`.


### Recursive Structuring

Converts unstructured data into structured data, recursively, according to your specification given as a type.
The following types are supported:

- `typing.Optional[T]` and its 3.10+ form, `T | None`.
- `list[T]`, `typing.List[T]`, `typing.MutableSequence[T]`, `typing.Sequence[T]` convert to a lists.
- `tuple` and `typing.Tuple` (both variants, `tuple[T, ...]` and `tuple[X, Y, Z]`).
- `set[T]`, `typing.MutableSet[T]`, and `typing.Set[T]` convert to a sets.
- `frozenset[T]`, and `typing.FrozenSet[T]` convert to a frozensets.
- `dict[K, V]`, `typing.Dict[K, V]`, `typing.MutableMapping[K, V]`, and `typing.Mapping[K, V]` convert to a dictionaries.
- [`typing.TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict), ordinary and generic.
- [`typing.NewType`](https://docs.python.org/3/library/typing.html#newtype)
- [PEP 695 type aliases](https://docs.python.org/3/library/typing.html#type-aliases) on 3.12+
- _attrs_ classes with simple attributes and the usual `__init__`[^simple].
- All _attrs_ classes and dataclasses with the usual `__init__`, if their complex attributes have type metadata.
- Unions of supported _attrs_ classes, given that all of the classes have a unique field.
- Unions of anything, if you provide a disambiguation function for it.
- Custom converters for any type can be registered using `register_structure_hook`.

[^simple]: Simple attributes are attributes that can be assigned unstructured data, like numbers, strings, and collections of unstructured data.


### Batteries Included

_cattrs_ comes with pre-configured converters for a number of serialization libraries, including JSON (standard library, [_orjson_](https://pypi.org/project/orjson/), [UltraJSON](https://pypi.org/project/ujson/)), [_msgpack_](https://pypi.org/project/msgpack/), [_cbor2_](https://pypi.org/project/cbor2/), [_bson_](https://pypi.org/project/bson/), [PyYAML](https://pypi.org/project/PyYAML/), [_tomlkit_](https://pypi.org/project/tomlkit/) and [_msgspec_](https://pypi.org/project/msgspec/) (supports only JSON at this time).

For details, see the [cattrs.preconf package](https://catt.rs/en/stable/preconf.html).


## Design Decisions

_cattrs_ is based on a few fundamental design decisions:

- Un/structuring rules are separate from the models.
  This allows models to have a one-to-many relationship with un/structuring rules, and to create un/structuring rules for models which you do not own and you cannot change.
  (_cattrs_ can be configured to use un/structuring rules from models using the [`use_class_methods` strategy](https://catt.rs/en/latest/strategies.html#using-class-specific-structure-and-unstructure-methods).)
- Invent as little as possible; reuse existing ordinary Python instead.
  For example, _cattrs_ did not have a custom exception type to group exceptions until the sanctioned Python [`exceptiongroups`](https://docs.python.org/3/library/exceptions.html#ExceptionGroup).
  A side-effect of this design decision is that, in a lot of cases, when you're solving _cattrs_ problems you're actually learning Python instead of learning _cattrs_.
- Resist the temptation to guess.
  If there are two ways of solving a problem, _cattrs_ should refuse to guess and let the user configure it themselves.

A foolish consistency is the hobgoblin of little minds, so these decisions can and are sometimes broken, but they have proven to be a good foundation.


<!-- end-why -->

## Credits

Major credits to Hynek Schlawack for creating [attrs](https://attrs.org) and its predecessor, [characteristic](https://github.com/hynek/characteristic).

_cattrs_ is tested with [Hypothesis](http://hypothesis.readthedocs.io/en/latest/), by David R. MacIver.

_cattrs_ is benchmarked using [perf](https://github.com/haypo/perf) and [pytest-benchmark](https://pytest-benchmark.readthedocs.io/en/latest/index.html).

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [`audreyr/cookiecutter-pypackage`](https://github.com/audreyr/cookiecutter-pypackage) project template.
