# Converters

All _cattrs_ functionality is exposed through a {class}`cattrs.Converter` object.
Global _cattrs_ functions, such as {meth}`cattrs.unstructure`, use a single global converter.
Changes done to this global converter, such as registering new structure and unstructure hooks, affect all code using the global functions.

## Global Converter

A global converter is provided for convenience as `cattrs.global_converter`.
The following functions implicitly use this global converter:

- {meth}`cattrs.structure`
- {meth}`cattrs.unstructure`
- {meth}`cattrs.structure_attrs_fromtuple`
- {meth}`cattrs.structure_attrs_fromdict`

Changes made to the global converter will affect the behavior of these functions.

Larger applications are strongly encouraged to create and customize a different, private instance of {class}`cattrs.Converter`.

## Converter Objects

To create a private converter, simply instantiate a {class}`cattrs.Converter`.

The core functionality of a converter is [structuring](structuring.md) and [unstructuring](unstructuring.md) data by composing provided and [custom handling functions](customizing.md), called _hooks_.

Currently, a converter contains the following state:

- a registry of unstructure hooks, backed by a [singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch) and a `function_dispatch`.
- a registry of structure hooks, backed by a different singledispatch and `function_dispatch`.
- a LRU cache of union disambiguation functions.
- a reference to an unstructuring strategy (either AS_DICT or AS_TUPLE).
- a `dict_factory` callable, used for creating `dicts` when dumping _attrs_ classes using `AS_DICT`.

Converters may be cloned using the {meth}`Converter.copy() <cattrs.BaseConverter.copy>` method.
The new copy may be changed through the `copy` arguments, but will retain all manually registered hooks from the original.

### Fallback Hook Factories

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
...     unstructure_fallback_factory=parent._unstructure_func.dispatch, 
...     structure_fallback_factory=parent._structure_func.dispatch,
... )
```

```{note}
`Converter._structure_func.dispatch` and `Converter._unstructure_func.dispatch` are slated to become public APIs in a future release.
```

```{versionadded} 23.2.0

```

## `cattrs.Converter`

The {class}`Converter <cattrs.Converter>` is a converter variant that automatically generates, compiles and caches specialized structuring and unstructuring hooks for _attrs_ classes, dataclasses and TypedDicts.

`Converter` differs from the {class}`cattrs.BaseConverter` in the following ways:

- structuring and unstructuring of _attrs_ classes is slower the first time, but faster every subsequent time
- structuring and unstructuring can be customized
- support for _attrs_ classes with PEP563 (postponed) annotations
- support for generic _attrs_ classes
- support for easy overriding collection unstructuring

The `Converter` used to be called `GenConverter`, and that alias is still present for backwards compatibility reasons.

## `cattrs.BaseConverter`

The {class}`BaseConverter <cattrs.BaseConverter>` is a simpler and slower `Converter` variant.
It does no code generation, so it may be faster on first-use which can be useful in specific cases, like CLI applications where startup time is more important than throughput.
