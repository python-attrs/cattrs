# Customizing Class Un/structuring

This section deals with customizing the unstructuring and structuring processes in _cattrs_.

## Using `cattrs.Converter`

The default {class}`Converter <cattrs.Converter>`, upon first encountering an _attrs_ class, will use the generation functions mentioned here to generate the specialized hooks for it, register the hooks and use them.

## Manual Un/structuring Hooks

You can write your own structuring and unstructuring functions and register
them for types using {meth}`Converter.register_structure_hook() <cattrs.BaseConverter.register_structure_hook>` and
{meth}`Converter.register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>`. This approach is the most
flexible but also requires the most amount of boilerplate.

## Using `cattrs.gen` Generators

_cattrs_ includes a module, {mod}`cattrs.gen`, which allows for generating and compiling specialized functions for unstructuring _attrs_ classes.

One reason for generating these functions in advance is that they can bypass a lot of _cattrs_ machinery and be significantly faster than normal _cattrs_.

Another reason is that it's possible to override behavior on a per-attribute basis.

Currently, the overrides only support generating dictionary un/structuring functions (as opposed to tuples), and support `omit_if_default`, `forbid_extra_keys`, `rename` and `omit`.

### `omit_if_default`

This override can be applied on a per-class or per-attribute basis.
The generated unstructuring function will skip unstructuring values that are equal to their default or factory values.

```{doctest}

>>> from cattrs.gen import make_dict_unstructure_fn, override
>>>
>>> @define
... class WithDefault:
...    a: int
...    b: dict = Factory(dict)
>>>
>>> c = cattrs.Converter()
>>> c.register_unstructure_hook(WithDefault, make_dict_unstructure_fn(WithDefault, c, b=override(omit_if_default=True)))
>>> c.unstructure(WithDefault(1))
{'a': 1}
```

Note that the per-attribute value overrides the per-class value. A side-effect
of this is the ability to force the presence of a subset of fields.
For example, consider a class with a `DateTime` field and a factory for it:
skipping the unstructuring of the `DateTime` field would be inconsistent and
based on the current time. So we apply the `omit_if_default` rule to the class,
but not to the `DateTime` field.

```{note}
    The parameter to `make_dict_unstructure_function` is named ``_cattrs_omit_if_default`` instead of just ``omit_if_default`` to avoid potential collisions with an override for a field named ``omit_if_default``.
```

```{doctest}

>>> from pendulum import DateTime
>>> from cattrs.gen import make_dict_unstructure_fn, override
>>>
>>> @define
... class TestClass:
...     a: Optional[int] = None
...     b: DateTime = Factory(DateTime.utcnow)
>>>
>>> c = cattrs.Converter()
>>> hook = make_dict_unstructure_fn(TestClass, c, _cattrs_omit_if_default=True, b=override(omit_if_default=False))
>>> c.register_unstructure_hook(TestClass, hook)
>>> c.unstructure(TestClass())
{'b': ...}
```

This override has no effect when generating structuring functions.

### `forbid_extra_keys`

By default _cattrs_ is lenient in accepting unstructured input.
If extra keys are present in a dictionary, they will be ignored when generating a structured object.
Sometimes it may be desirable to enforce a stricter contract, and to raise an error when unknown keys are present - in particular when fields have default values this may help with catching typos.
`forbid_extra_keys` can also be enabled (or disabled) on a per-class basis when creating structure hooks with {py:func}`make_dict_structure_fn() <cattrs.gen.make_dict_structure_fn>`.

```{doctest}
    :options: +SKIP

>>> from cattrs.gen import make_dict_structure_fn
>>>
>>> @define
... class TestClass:
...    number: int = 1
>>>
>>> c = cattrs.Converter(forbid_extra_keys=True)
>>> c.structure({"nummber": 2}, TestClass)
Traceback (most recent call last):
...
ForbiddenExtraKeyError: Extra fields in constructor for TestClass: nummber
>>> hook = make_dict_structure_fn(TestClass, c, _cattrs_forbid_extra_keys=False)
>>> c.register_structure_hook(TestClass, hook)
>>> c.structure({"nummber": 2}, TestClass)
TestClass(number=1)
```

This behavior can only be applied to classes or to the default for the {class}`Converter <cattrs.Converter>`, and has no effect when generating unstructuring functions.

```{versionchanged} 23.2.0
The value for the `make_dict_structure_fn._cattrs_forbid_extra_keys` parameter is now taken from the given converter by default.
```


### `rename`

Using the rename override makes `cattrs` simply use the provided name instead
of the real attribute name. This is useful if an attribute name is a reserved
keyword in Python.

```{doctest}

>>> from pendulum import DateTime
>>> from cattrs.gen import make_dict_unstructure_fn, make_dict_structure_fn, override
>>>
>>> @define
... class ExampleClass:
...     klass: Optional[int]
>>>
>>> c = cattrs.Converter()
>>> unst_hook = make_dict_unstructure_fn(ExampleClass, c, klass=override(rename="class"))
>>> st_hook = make_dict_structure_fn(ExampleClass, c, klass=override(rename="class"))
>>> c.register_unstructure_hook(ExampleClass, unst_hook)
>>> c.register_structure_hook(ExampleClass, st_hook)
>>> c.unstructure(ExampleClass(1))
{'class': 1}
>>> c.structure({'class': 1}, ExampleClass)
ExampleClass(klass=1)
```

### `omit`

This override can only be applied to individual attributes. 
Using the `omit` override will simply skip the attribute completely when generating a structuring or unstructuring function.

```{doctest}

>>> from cattrs.gen import make_dict_unstructure_fn, override
>>>
>>> @define
... class ExampleClass:
...     an_int: int
>>>
>>> c = cattrs.Converter()
>>> unst_hook = make_dict_unstructure_fn(ExampleClass, c, an_int=override(omit=True))
>>> c.register_unstructure_hook(ExampleClass, unst_hook)
>>> c.unstructure(ExampleClass(1))
{}
```

### `struct_hook` and `unstruct_hook`

By default, the generators will determine the right un/structure hook for each attribute of a class at time of generation according to the type of each individual attribute.

This process can be overriden by passing in the desired un/structure manually.

```{doctest}

>>> from cattrs.gen import make_dict_structure_fn, override

>>> @define
... class ExampleClass:
...     an_int: int

>>> c = cattrs.Converter()
>>> st_hook = make_dict_structure_fn(
...     ExampleClass, c, an_int=override(struct_hook=lambda v, _: v + 1)
... )
>>> c.register_structure_hook(ExampleClass, st_hook)

>>> c.structure({"an_int": 1}, ExampleClass)
ExampleClass(an_int=2)
```

### `use_alias`

By default, fields are un/structured to and from dictionary keys exactly matching the field names.
_attrs_ classes support field aliases, which override the `__init__` parameter name for a given field.
By generating your un/structure function with `_cattrs_use_alias=True`, _cattrs_ will use the field alias instead of the field name as the un/structured dictionary key.

```{doctest}

>>> from cattrs.gen import make_dict_structure_fn
>>>
>>> @define
... class AliasClass:
...    number: int = field(default=1, alias="count")
>>>
>>> c = cattrs.Converter()
>>> hook = make_dict_structure_fn(AliasClass, c, _cattrs_use_alias=True)
>>> c.register_structure_hook(AliasClass, hook)
>>> c.structure({"count": 2}, AliasClass)
AliasClass(number=2)
```

```{versionadded} 23.2.0

```

### `include_init_false`

By default, _attrs_ fields defined as `init=False` are skipped when un/structuring.
By generating your un/structure function with `_cattrs_include_init_false=True`, all `init=False` fields will be included for un/structuring.

```{doctest}

>>> from cattrs.gen import make_dict_structure_fn
>>>
>>> @define
... class ClassWithInitFalse:
...    number: int = field(default=1, init=False)
>>>
>>> c = cattrs.Converter()
>>> hook = make_dict_structure_fn(ClassWithInitFalse, c, _cattrs_include_init_false=True)
>>> c.register_structure_hook(ClassWithInitFalse, hook)
>>> c.structure({"number": 2}, ClassWithInitFalse)
ClassWithInitFalse(number=2)
```

A single attribute can be included by overriding it with `omit=False`.

```{doctest}

>>> c = cattrs.Converter()
>>> hook = make_dict_structure_fn(ClassWithInitFalse, c, number=override(omit=False))
>>> c.register_structure_hook(ClassWithInitFalse, hook)
>>> c.structure({"number": 2}, ClassWithInitFalse)
ClassWithInitFalse(number=2)
```

```{versionadded} 23.2.0

```
