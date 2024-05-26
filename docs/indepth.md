# Converters In-Depth
```{currentmodule} cattrs
```

Converters are registries of rules _cattrs_ uses to perform function composition and generate its un/structuring functions.

Currently, a converter contains the following state:

- a registry of unstructure hooks, backed by a [singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch) and a {class}`FunctionDispatch <cattrs.dispatch.FunctionDispatch>`, wrapped in a [cache](https://docs.python.org/3/library/functools.html#functools.cache).
- a registry of structure hooks, backed by a different singledispatch and `FunctionDispatch`, and a different cache.
- a `detailed_validation` flag (defaulting to true), determining whether the converter uses [detailed validation](validation.md#detailed-validation).
- a reference to {class}`an unstructuring strategy <cattrs.UnstructureStrategy>` (either AS_DICT or AS_TUPLE).
- a `prefer_attrib_converters` flag (defaulting to false), determining whether to favor _attrs_ converters over normal _cattrs_ machinery when structuring _attrs_ classes
- a `dict_factory` callable, a legacy parameter used for creating `dicts` when dumping _attrs_ classes using `AS_DICT`.

Converters may be cloned using the {meth}`Converter.copy() <cattrs.BaseConverter.copy>` method.
The new copy may be changed through the `copy` arguments, but will retain all manually registered hooks from the original.


## Customizing Collection Unstructuring

```{important}
This feature is supported for Python 3.9 and later.
```

```{tip}
See [](customizing.md#customizing-collections) for a more modern and more powerful way of customizing collection handling.
```

Overriding collection unstructuring in a generic way can be a very useful feature.
A common example is using a JSON library that doesn't support sets, but expects lists and tuples instead.

Using ordinary unstructuring hooks for this is unwieldy due to the semantics of
[singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch);
in other words, you'd need to register hooks for all specific types of set you're using (`set[int]`, `set[float]`,
`set[str]`...), which is not useful.

Function-based hooks can be used instead, but come with their own set of challenges - they're complicated to write efficiently.

The {class}`Converter` supports easy customizations of collection unstructuring using its `unstruct_collection_overrides` parameter.
For example, to unstructure all sets into lists, use the following:

```{doctest}

>>> from collections.abc import Set
>>> converter = cattrs.Converter(unstruct_collection_overrides={Set: list})

>>> converter.unstructure({1, 2, 3})
[1, 2, 3]
```

Going even further, the `Converter` contains heuristics to support the following Python types, in order of decreasing generality:

- `typing.Sequence`, `typing.MutableSequence`, `list`, `deque`, `tuple`
- `typing.Set`, `frozenset`, `typing.MutableSet`, `set`
- `typing.Mapping`, `typing.MutableMapping`, `dict`, `defaultdict`, `collections.OrderedDict`, `collections.Counter`

For example, if you override the unstructure type for `Sequence`, but not for `MutableSequence`, `list` or `tuple`, the override will also affect those types.
An easy way to remember the rule:

- all `MutableSequence` s are `Sequence` s, so the override will apply
- all `list` s are `MutableSequence` s, so the override will apply
- all `tuple` s are `Sequence` s, so the override will apply

If, however, you override only `MutableSequence`, fields annotated as `Sequence` will not be affected (since not all sequences are mutable sequences), and fields annotated as tuples will not be affected (since tuples
are not mutable sequences in the first place).

Similar logic applies to the set and mapping hierarchies.

Make sure you're using the types from `collections.abc` on Python 3.9+, and from `typing` on older Python versions.


## Fallback Hook Factories

By default, when a {class}`converter <cattrs.BaseConverter>` cannot handle a type it will:

* when unstructuring, pass the value through unchanged
* when structuring, raise a {class}`cattrs.errors.StructureHandlerNotFoundError` asking the user to add configuration

These behaviors can be customized by providing custom [hook factories](usage.md#using-factory-hooks) when creating the converter.

```python
>>> from pickle import dumps

>>> class Unsupported:
...     """An artisinal (non-attrs) class, unsupported by default."""

>>> converter = Converter(unstructure_fallback_factory=lambda _: dumps)
>>> instance = Unsupported()
>>> converter.unstructure(instance)
b'\x80\x04\x95\x18\x00\x00\x00\x00\x00\x00\x00\x8c\x08__main__\x94\x8c\x04Test\x94\x93\x94)\x81\x94.'
```

This also enables converters to be chained.

```python
>>> parent = Converter()

>>> child = Converter(
...     unstructure_fallback_factory=parent.get_unstructure_hook,
...     structure_fallback_factory=parent.get_structure_hook,
... )
```

```{versionadded} 23.2.0

```

## `cattrs.Converter`

The {class}`Converter` is a converter variant that automatically generates, compiles and caches specialized structuring and unstructuring hooks for _attrs_ classes, dataclasses and TypedDicts.

`Converter` differs from the {class}`cattrs.BaseConverter` in the following ways:

- structuring and unstructuring of _attrs_ classes is slower the first time, but faster every subsequent time
- structuring and unstructuring can be customized
- support for _attrs_ classes with PEP563 (postponed) annotations
- support for generic _attrs_ classes
- support for easy overriding collection unstructuring

The {class}`Converter` used to be called `GenConverter`, and that alias is still present for backwards compatibility.

## `cattrs.BaseConverter`

The {class}`BaseConverter` is a simpler and slower converter variant.
It does no code generation, so it may be faster on first-use which can be useful in specific cases, like CLI applications where startup time is more important than throughput.
