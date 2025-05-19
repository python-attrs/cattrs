# The Basics
```{currentmodule} cattrs
```

All _cattrs_ functionality is exposed through a {class}`cattrs.Converter` object.
A global converter is provided for convenience as {data}`cattrs.global_converter`
but more complex customizations should be performed on private instances, any number of which can be made.


## Converters and Hooks

The core functionality of a converter is structuring and unstructuring data by composing [provided](defaulthooks.md) and [custom handling functions](customizing.md), called _hooks_.

To create a private converter, instantiate a {class}`cattrs.Converter`. Converters are relatively cheap; users are encouraged to have as many as they need.

The two main methods, {meth}`structure <cattrs.BaseConverter.structure>` and {meth}`unstructure <cattrs.BaseConverter.unstructure>`, are used to convert between _structured_ and _unstructured_ data.

```{doctest} basics
>>> from cattrs import structure, unstructure
>>> from attrs import define

>>> @define
... class Model:
...    a: int

>>> unstructure(Model(1))
{'a': 1}
>>> structure({"a": 1}, Model)
Model(a=1)
```

_cattrs_ comes with a rich library of un/structuring hooks by default but it excels at composing custom hooks with built-in ones.

The simplest approach to customization is writing a new hook from scratch.
For example, we can write our own hook for the `int` class and register it to a converter.

```{doctest} basics
>>> from cattrs import Converter

>>> converter = Converter()

>>> @converter.register_structure_hook
... def int_hook(value, type) -> int:
...     if not isinstance(value, int):
...         raise ValueError('not an int!')
...     return value
```

Now, any other hook converting an `int` will use it.

Another approach to customization is wrapping (composing) an existing hook with your own function.
A base hook can be obtained from a converter and then be subjected to the very rich machinery of function composition that Python offers.


```{doctest} basics
>>> base_hook = converter.get_structure_hook(Model)

>>> @converter.register_structure_hook
... def my_model_hook(value, type) -> Model:
...     # Apply any preprocessing to the value.
...     result = base_hook(value, type)
...     # Apply any postprocessing to the model.
...     return result
```

(`cattrs.structure({}, Model)` is equivalent to `cattrs.get_structure_hook(Model)({}, Model)`.)

Now if we use this hook to structure a `Model`, through ✨the magic of function composition✨ that hook will use our old `int_hook`.

```python
>>> converter.structure({"a": "1"}, Model)
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

Global _cattrs_ functions, such as {meth}`cattrs.structure`, use a single {data}`global converter <cattrs.global_converter>`.
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
