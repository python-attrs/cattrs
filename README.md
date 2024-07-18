# *cattrs*: Flexible Object Serialization and Validation

<p>
  <em>Because validation belongs to the edges.</em>
</p>

[![Documentation](https://img.shields.io/badge/Docs-Read%20The%20Docs-black)](https://catt.rs/)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/cattrs.svg)](https://pypi.python.org/pypi/cattrs)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/cattrs.svg)](https://github.com/python-attrs/cattrs)
[![Downloads](https://static.pepy.tech/badge/cattrs/month)](https://pepy.tech/project/cattrs)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Tinche/22405310d6a663164d894a2beab4d44d/raw/covbadge.json)](https://github.com/python-attrs/cattrs/actions/workflows/main.yml)

---

**cattrs** is a Swiss Army knife for (un)structuring and validating data in Python.
In practice, that means it converts **unstructured dictionaries** into **proper classes** and back, while **validating** their contents.

---

Python has a rich set of powerful, easy to use, built-in **unstructured** data types like dictionaries, lists and tuples.
These data types effortlessly convert into common serialization formats like JSON, MessagePack, CBOR, YAML or TOML.

But the data that is used by your **business logic** should be **structured** into well-defined classes, since not all combinations of field names or values are valid inputs to your programs.
The more trust you can have into the structure of your data, the simpler your code can be, and the fewer edge cases you have to worry about.

When you're handed unstructured data (by your network, file system, database, ...), _cattrs_ helps to convert this data into trustworthy structured data.
When you have to convert your structured data into data types that other libraries can handle, _cattrs_ turns your classes and enumerations into dictionaries, integers and strings.

_attrs_ (and to a certain degree dataclasses) are excellent libraries for declaratively describing the structure of your data, but they're purposefully not serialization libraries.
*cattrs* is there for you the moment your `attrs.asdict(your_instance)` and `YourClass(**data)` start failing you because you need more control over the conversion process.


## Examples

_cattrs_ works best with [_attrs_](https://www.attrs.org/) classes, and [dataclasses](https://docs.python.org/3/library/dataclasses.html) where simple (un-)structuring works out of the box, even for nested data:

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

> [!IMPORTANT]
> Note how the structuring and unstructuring details do **not** pollute your class, meaning: your data model.
> Any needs to configure the conversion are done within *cattrs* itself, not within your data model.
>
> There are popular validation libraries for Python that couple your data model with its validation and serialization rules based on, for example, web APIs.
> We think that's the wrong approach.
> Validation and serializations are concerns of the edges of your program – not the core.
> They should neither apply design pressure on your business code, nor affect the performance of your code through unnecessary validation.
> In bigger real-world code bases it's also common for data coming from multiple sources that need different validation and serialization rules.
>
> 🎶 You gotta keep 'em separated. 🎶

*cattrs* also works with the usual Python collection types like dictionaries, lists, or tuples when you want to **normalize** unstructured data data into a certain (still unstructured) shape.
For example, to convert a list of a float, an int and a string into a tuple of ints:

```python
>>> import cattrs

>>> cattrs.structure([1.0, 2, "3"], tuple[int, int, int])
(1, 2, 3)

```

Finally, here's a much more complex example, involving _attrs_ classes where _cattrs_ interprets the type annotations to structure and unstructure the data correctly, including Enums and nested data structures:

```python
>>> from enum import unique, Enum
>>> from typing import Optional, Sequence, Union
>>> from cattrs import structure, unstructure
>>> from attrs import define, field

>>> @unique
... class CatBreed(Enum):
...     SIAMESE = "siamese"
...     MAINE_COON = "maine_coon"
...     SACRED_BIRMAN = "birman"

>>> @define
... class Cat:
...     breed: CatBreed
...     names: Sequence[str]

>>> @define
... class DogMicrochip:
...     chip_id = field()  # Type annotations are optional, but recommended
...     time_chipped: float = field()

>>> @define
... class Dog:
...     cuteness: int
...     chip: DogMicrochip | None = None

>>> p = unstructure([Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)),
...                  Cat(breed=CatBreed.MAINE_COON, names=('Fluffly', 'Fluffer'))])

>>> p
[{'cuteness': 1, 'chip': {'chip_id': 1, 'time_chipped': 10.0}}, {'breed': 'maine_coon', 'names': ['Fluffly', 'Fluffer']}]
>>> structure(p, list[Union[Dog, Cat]])
[Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)), Cat(breed=<CatBreed.MAINE_COON: 'maine_coon'>, names=['Fluffly', 'Fluffer'])]

```

> [!TIP]
> Consider unstructured data a low-level representation that needs to be converted to structured data to be handled, and use `structure()`.
> When you're done, `unstructure()` the data to its unstructured form and pass it along to another library or module.
>
> Use [*attrs* type metadata](http://attrs.readthedocs.io/en/stable/examples.html#types) to add type metadata to attributes, so _cattrs_ will know how to structure and destructure them.


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

_cattrs_ comes with pre-configured converters for a number of serialization libraries, including JSON (standard library, [_orjson_](https://pypi.org/project/orjson/), [UltraJSON](https://pypi.org/project/ujson/)), [_msgpack_](https://pypi.org/project/msgpack/), [_cbor2_](https://pypi.org/project/cbor2/), [_bson_](https://pypi.org/project/bson/), [PyYAML](https://pypi.org/project/PyYAML/), [_tomlkit_](https://pypi.org/project/tomlkit/) and [_msgspec_](https://pypi.org/project/msgspec/) (supports JSON, MessagePack, YAML, and TOML).

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


## Additional documentation and talks

- [On structured and unstructured data, or the case for cattrs](https://threeofwands.com/on-structured-and-unstructured-data-or-the-case-for-cattrs/)
- [Why I use attrs instead of pydantic](https://threeofwands.com/why-i-use-attrs-instead-of-pydantic/)
- [cattrs I: un/structuring speed](https://threeofwands.com/why-cattrs-is-so-fast/)
- [Python has a macro language - it's Python (PyCon IT 2022)](https://www.youtube.com/watch?v=UYRSixikUTo)
- [Intro to cattrs 23.1](https://threeofwands.com/intro-to-cattrs-23-1-0/)


## Credits

Major credits to Hynek Schlawack for creating [attrs](https://attrs.org) and its predecessor, [characteristic](https://github.com/hynek/characteristic).

_cattrs_ is tested with [Hypothesis](http://hypothesis.readthedocs.io/en/latest/), by David R. MacIver.

_cattrs_ is benchmarked using [perf](https://github.com/haypo/perf) and [pytest-benchmark](https://pytest-benchmark.readthedocs.io/en/latest/index.html).

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [`audreyr/cookiecutter-pypackage`](https://github.com/audreyr/cookiecutter-pypackage) project template.
