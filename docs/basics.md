# The Basics
```{currentmodule} cattrs
```

All _cattrs_ functionality is exposed through a {class}`cattrs.Converter` object.
A global converter is provided for convenience as {data}`cattrs.global_converter` but more complex customizations should be performed on private instances.


## Converters

The core functionality of a converter is [structuring](structuring.md) and [unstructuring](unstructuring.md) data by composing provided and [custom handling functions](customizing.md), called _hooks_.

To create a private converter, instantiate a {class}`cattrs.Converter`. Converters are relatively cheap; users are encouraged to have as many as they need.

The two main methods are {meth}`structure <cattrs.BaseConverter.structure>` and {meth}`unstructure <cattrs.BaseConverter.unstructure>`, these are used to convert between _structured_ and _unstructured_ data.

```python
>>> from cattrs import structure, unstructure
>>> from attrs import define

>>> @define
... class Model:
...    a: int

>>> unstructure(Model(1))
{"a": 1}
>>> structure({"a": 1}, Model)
Model(a=1)
```

_cattrs_ comes with a rich library of un/structuring rules by default, but it excels at composing custom rules with built-in ones.

The simplest approach to customization is wrapping an existing hook with your own function.
A base hook can be obtained from a converter and be subjected to the very rich machinery of function composition in Python.

```python
>>> from cattrs import get_structure_hook

>>> base_hook = get_structure_hook(Model)

>>> def my_hook(value, type):
...     # Apply any preprocessing to the value.
...     result = base_hook(value, type)
...     # Apply any postprocessing to the value.
...     return result
```

This new hook can be used directly or registered to a converter (the original instance, or a different one).

(`cattrs.structure({}, Model)` is shorthand for `cattrs.get_structure_hook(Model)({}, Model)`.)

Another approach is to write a hook from scratch instead of wrapping an existing one.
For example, we can write our own hook for the `int` class.

```python
>>> def my_int_hook(value, type):
...     if not isinstance(value, int):
...         raise ValueError('not an int!')
...     return value
```

We can then register this hook to a converter, and any other hook converting an `int` will use it.
Since this is an impactful change, we will switch to using a private converter.

```python
>>> from cattrs import Converter

>>> c = Converter()

>>> c.register_structure_hook(int, my_int_hook)
```

Now, if we ask our new converter for a `Model` hook, through the ✨magic of function composition✨ that hook will use our new `my_int_hook`.

```python
>>> base_hook = c.get_structure_hook(Model)
>>> base_hook({"a": "1"}, Model)
  + Exception Group Traceback (most recent call last):
    |   File "...", line 22, in <module>
    |     base_hook({"a": "1"}, Model)
    |   File "<cattrs generated structure __main__.Model>", line 9, in structure_Model
    | cattrs.errors.ClassValidationError: While structuring Model (1 sub-exception)
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "<cattrs generated structure __main__.Model>", line 5, in structure_Model
      |   File "...", line 15, in my_int_hook
      |     raise ValueError("not an int!")
      | ValueError: not an int!
      | Structuring class Model @ attribute a
      +------------------------------------
```

To continue reading about customizing _cattrs_, see [](customizing.md).
More advanced structuring customizations are commonly called [](strategies.md).

## Global Converter

Global _cattrs_ functions, such as {meth}`cattrs.unstructure`, use a single {data}`global converter <cattrs.global_converter>`.
Changes done to this global converter, such as registering new structure and unstructure hooks, affect all code using the global functions.

The following functions implicitly use this global converter:

- {meth}`cattrs.structure`
- {meth}`cattrs.unstructure`
- {meth}`cattrs.get_structure_hook`
- {meth}`cattrs.get_unstructure_hook`
- {meth}`cattrs.structure_attrs_fromtuple`
- {meth}`cattrs.structure_attrs_fromdict`

Changes made to the global converter will affect the behavior of these functions.

Larger applications are strongly encouraged to create and customize different, private instances of {class}`cattrs.Converter`.
