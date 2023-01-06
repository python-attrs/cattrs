# Converters

All _cattrs_ functionality is exposed through a {class}`cattrs.Converter` object.
Global _cattrs_ functions, such as {meth}`cattrs.unstructure`, use a single
global converter. Changes done to this global converter, such as registering new
structure and unstructure hooks, affect all code using the global
functions.

## Global converter

A global converter is provided for convenience as `cattrs.global_converter`.
The following functions implicitly use this global converter:

- {meth}`cattrs.structure`
- {meth}`cattrs.unstructure`
- {meth}`cattrs.structure_attrs_fromtuple`
- {meth}`cattrs.structure_attrs_fromdict`

Changes made to the global converter will affect the behavior of these functions.

Larger applications are strongly encouraged to create and customize a different,
private instance of {class}`cattrs.Converter`.

## Converter objects

To create a private converter, simply instantiate a {class}`cattrs.Converter`.
Currently, a converter contains the following state:

- a registry of unstructure hooks, backed by a [singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch) and a `function_dispatch`.
- a registry of structure hooks, backed by a different singledispatch and `function_dispatch`.
- a LRU cache of union disambiguation functions.
- a reference to an unstructuring strategy (either AS_DICT or AS_TUPLE).
- a `dict_factory` callable, used for creating `dicts` when dumping _attrs_ classes using `AS_DICT`.

Converters may be cloned using the {meth}`cattrs.Converter.copy` method.
The new copy may be changed through the `copy` arguments, but will retain all manually registered hooks from the original.

## `cattrs.Converter`

The {class}`Converter <cattrs.Converter>` is a converter variant that automatically generates,
compiles and caches specialized structuring and unstructuring hooks for _attrs_
classes and dataclasses.

`Converter` differs from the {class}`cattrs.BaseConverter` in the following ways:

- structuring and unstructuring of _attrs_ classes is slower the first time, but faster every subsequent time
- structuring and unstructuring can be customized
- support for _attrs_ classes with PEP563 (postponed) annotations
- support for generic _attrs_ classes
- support for easy overriding collection unstructuring

The `Converter` used to be called `GenConverter`, and that alias is still present for backwards compatibility reasons.

## `cattrs.BaseConverter`

The {class}`BaseConverter <cattrs.BaseConverter>` is a simpler and slower Converter variant. It does no
code generation, so it may be faster on first-use which can be useful
in specific cases, like CLI applications where startup time is more
important than throughput.
