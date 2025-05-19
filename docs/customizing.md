# Customizing (Un-)structuring

This section describes customizing the unstructuring and structuring processes in _cattrs_.

As you go about customizing converters by registering hooks and hook factories,
keep in mind that **the order of hook registration matters**.

Technically speaking, whether the order matters or not depends on the actual implementation of hook factories used.
In practice, the built-in _cattrs_ hooks are optimized to perform early resolution of hooks.
You will likely compose with these hook factories.

This means that **hooks for simpler types should be registered first**.
For example, to override hooks for structuring `int` and `list[int]`, the hook for `int`
must be registered first.
When the {meth}`list_structure_factory() <cattrs.cols.list_structure_factory>`
is applied to the `list[int]` type to produce a hook, it will retrieve and store
the hook for `int`, which should be already present.

## Custom (Un-)structuring Hooks

You can write your own structuring and unstructuring functions and register them for types using {meth}`Converter.register_structure_hook() <cattrs.BaseConverter.register_structure_hook>` and {meth}`Converter.register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>`.

{meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>` and {meth}`register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>` use a Python [_singledispatch_](https://docs.python.org/3/library/functools.html#functools.singledispatch) under the hood.
_singledispatch_ is powerful and fast but comes with some limitations; namely that it performs checks using `issubclass()` which doesn't work with many Python types.
Some examples of this are:

- various generic collections (`list[int]` is not a _subclass_ of `list`)
- literals (`Literal[1]` is not a _subclass_ of `Literal[1]`)
- generics (`MyClass[int]` is not a _subclass_ of `MyClass`)
- protocols, unless they are `runtime_checkable`
- various modifiers, such as `Final` and `NotRequired`
- `typing.Annotated`

... and many others. In these cases, [predicate hooks](#predicate-hooks) should be used instead.

Even though unions, [newtypes](https://docs.python.org/3/library/typing.html#newtype)
and [modern type aliases](https://docs.python.org/3/library/typing.html#type-aliases)
do not work with _singledispatch_,
these methods have special support for these type forms and can be used with them.
Instead of using _singledispatch_, predicate hooks will automatically be used instead.

### Use as Decorators

{meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>` and {meth}`register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>` can also be used as _decorators_.
When used this way they behave a little differently.

{meth}`register_structure_hook() <cattrs.BaseConverter.register_structure_hook>` will inspect the return type of the hook and register the hook for that type.

```python
@converter.register_structure_hook
def my_int_hook(val: Any, _) -> int:
    """This hook will be registered for `int`s."""
    return int(val)
```

{meth}`register_unstructure_hook() <cattrs.BaseConverter.register_unstructure_hook>` will inspect the type of the first argument and register the hook for that type.

```python
from datetime import datetime

@converter.register_unstructure_hook
def my_datetime_hook(val: datetime) -> str:
    """This hook will be registered for `datetime`s."""
    return val.isoformat()
```

The non-decorator approach is still recommended when dealing with lambdas, hooks produced elsewhere, unannotated hooks and situations where type introspection doesn't work.

```{versionadded} 24.1.0

```

### Predicate Hooks

A _predicate_ is a function that takes a type and returns true or false
depending on whether the associated hook can handle the given type.

The {meth}`register_unstructure_hook_func() <cattrs.BaseConverter.register_unstructure_hook_func>` and {meth}`register_structure_hook_func() <cattrs.BaseConverter.register_structure_hook_func>` are used
to link un/structuring hooks to arbitrary types. These hooks are then called _predicate hooks_, and are very powerful.

Predicate hooks are evaluated after the _singledispatch_ hooks.
In the case where both a _singledispatch_ hook and a predicate hook are present, the _singledispatch_ hook will be used.
Predicate hooks are checked in reverse order of registration, one-by-one, until a match is found.

The following example demonstrates a predicate that checks for the presence of an attribute on a class (`custom`), and then overrides the structuring logic.

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

### Hook Factories

Hook factories are higher-order predicate hooks: they are functions that _produce_ hooks.
Hook factories are commonly used to create very optimized hooks by offloading part of the work into a separate, earlier step.

Hook factories are registered using {meth}`Converter.register_unstructure_hook_factory() <cattrs.BaseConverter.register_unstructure_hook_factory>` and {meth}`Converter.register_structure_hook_factory() <cattrs.BaseConverter.register_structure_hook_factory>`.

Here's an example showing how to use hook factories to apply the `forbid_extra_keys` to all attrs classes:

```python
>>> from attrs import define, has
>>> from cattrs import Converter
>>> from cattrs.gen import make_dict_structure_fn

>>> c = Converter()

>>> c.register_structure_hook_factory(
...     has,
...     lambda cl: make_dict_structure_fn(cl, c, _cattrs_forbid_extra_keys=True)
... )

>>> @define
... class E:
...    an_int: int

>>> c.structure({"an_int": 1, "else": 2}, E)
Traceback (most recent call last):
...
cattrs.errors.ForbiddenExtraKeysError: Extra fields in constructor for E: else
```

Hook factories can receive the current converter by exposing an additional required parameter.

A complex use case for hook factories is described over at [](usage.md#using-factory-hooks).

#### Use as Decorators

{meth}`register_unstructure_hook_factory() <cattrs.BaseConverter.register_unstructure_hook_factory>` and
{meth}`register_structure_hook_factory() <cattrs.BaseConverter.register_structure_hook_factory>` can also be used as decorators.

Here's an example of using an unstructure hook factory to handle unstructuring [queues](https://docs.python.org/3/library/queue.html#queue.Queue).

```{doctest}
>>> from queue import Queue
>>> from typing import get_origin
>>> from cattrs import Converter

>>> c = Converter()

>>> @c.register_unstructure_hook_factory(lambda t: get_origin(t) is Queue)
... def queue_hook_factory(cl: Any, converter: Converter) -> Callable:
...     type_arg = get_args(cl)[0]
...     elem_handler = converter.get_unstructure_hook(type_arg)
...
...     def unstructure_hook(v: Queue) -> list:
...         res = []
...         while not v.empty():
...             res.append(elem_handler(v.get_nowait()))
...         return res
...
...     return unstructure_hook

>>> q = Queue()
>>> q.put(1)
>>> q.put(2)

>>> c.unstructure(q, unstructure_as=Queue[int])
[1, 2]
```

## Using `cattrs.gen` Hook Factories

The {mod}`cattrs.gen` module contains [hook factories](#hook-factories) for un/structuring _attrs_ classes, dataclasses and typed dicts.
The default {class}`Converter <cattrs.Converter>`, upon first encountering one of these types,
will use the hook factories mentioned here to generate specialized hooks for it,
register the hooks and use them.

One reason for generating these hooks in advance is that they can bypass a lot of _cattrs_ machinery and be significantly faster than normal _cattrs_.
The hook factories are also good building blocks for more complex customizations.

Another reason is overriding behavior on a per-attribute basis.

Currently, the overrides only support generating dictionary un/structuring hooks (as opposed to tuples),
and support `omit_if_default`, `forbid_extra_keys`, `rename` and `omit`.

### `omit_if_default`

This override can be applied on a per-class or per-attribute basis.
The generated unstructuring hook will skip unstructuring values that are equal to their default or factory values.

```{doctest}

>>> from cattrs.gen import make_dict_unstructure_fn, override

>>> @define
... class WithDefault:
...    a: int
...    b: dict = Factory(dict)

>>> c = cattrs.Converter()
>>> c.register_unstructure_hook(WithDefault, make_dict_unstructure_fn(WithDefault, c, b=override(omit_if_default=True)))
>>> c.unstructure(WithDefault(1))
{'a': 1}
```

Note that the per-attribute value overrides the per-class value.
A side-effect of this is the ability to force the presence of a subset of fields.
For example, consider a class with a `dateTime` field and a factory for it: skipping the unstructuring of the `dateTime` field would be inconsistent and based on the current time.
So we apply the `omit_if_default` rule to the class, but not to the `dateTime` field.

```{note}
    The parameter to `make_dict_unstructure_function` is named ``_cattrs_omit_if_default`` instead of just ``omit_if_default`` to avoid potential collisions with an override for a field named ``omit_if_default``.
```

```{doctest}

>>> from datetime import datetime
>>> from cattrs.gen import make_dict_unstructure_fn, override

>>> @define
... class TestClass:
...     a: Optional[int] = None
...     b: datetime = Factory(datetime.utcnow)

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
`forbid_extra_keys` can also be enabled (or disabled) on a per-class basis when creating structure hooks with {meth}`make_dict_structure_fn() <cattrs.gen.make_dict_structure_fn>`.

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

Using the rename override makes `cattrs` use the provided name instead of the real attribute name.
This is useful if an attribute name is a reserved keyword in Python.

```{doctest}

>>> from pendulum import DateTime
>>> from cattrs.gen import make_dict_unstructure_fn, make_dict_structure_fn, override

>>> @define
... class ExampleClass:
...     klass: Optional[int]

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

This process can be overriden by passing in the desired un/structure hook manually.

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
_attrs_ classes support _attrs_ field aliases, which override the `__init__` parameter name for a given field.
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

## Customizing Collections

```{currentmodule} cattrs.cols

```

The {mod}`cattrs.cols` module contains predicates and hook factories useful for customizing collection handling.
These hook factories can be wrapped to apply complex customizations.

Available predicates are:

- {meth}`is_any_set`
- {meth}`is_frozenset`
- {meth}`is_set`
- {meth}`is_sequence`
- {meth}`is_mapping`
- {meth}`is_namedtuple`
- {meth}`is_defaultdict`

````{tip}
These predicates aren't _cattrs_-specific and may be useful in other contexts.
```{doctest} predicates
>>> from cattrs.cols import is_sequence

>>> is_sequence(list[str])
True
```
````

Available hook factories are:

- {meth}`iterable_unstructure_factory`
- {meth}`list_structure_factory`
- {meth}`namedtuple_structure_factory`
- {meth}`namedtuple_unstructure_factory`
- {meth}`namedtuple_dict_structure_factory`
- {meth}`namedtuple_dict_unstructure_factory`
- {meth}`mapping_structure_factory`
- {meth}`mapping_unstructure_factory`
- {meth}`defaultdict_structure_factory`

Additional predicates and hook factories will be added as requested.

For example, by default sequences are structured from any iterable into lists.
This may be too lax, and additional validation may be applied by wrapping the default list structuring hook factory.

```{testcode} list-customization
from cattrs.cols import is_sequence, list_structure_factory

c = Converter()

@c.register_structure_hook_factory(is_sequence)
def strict_list_hook_factory(type, converter):

    # First, we generate the default hook...
    list_hook = list_structure_factory(type, converter)

    # Then, we wrap it with a function of our own...
    def strict_list_hook(value, type):
        if not isinstance(value, list):
            raise ValueError("Not a list!")
        return list_hook(value, type)

    # And finally, we return our own composite hook.
    return strict_list_hook
```

Now, all sequence structuring will be stricter:

```{doctest} list-customization
>>> c.structure({"a", "b", "c"}, list[str])
Traceback (most recent call last):
    ...
ValueError: Not a list!
```

```{versionadded} 24.1.0

```

### Customizing Named Tuples

Named tuples can be un/structured using dictionaries using the {meth}`namedtuple_dict_structure_factory`
and {meth}`namedtuple_dict_unstructure_factory` hook factories.

To unstructure _all_ named tuples into dictionaries:

```{doctest} namedtuples
>>> from typing import NamedTuple

>>> from cattrs.cols import is_namedtuple, namedtuple_dict_unstructure_factory
>>> c = Converter()

>>> c.register_unstructure_hook_factory(is_namedtuple, namedtuple_dict_unstructure_factory)
<function namedtuple_dict_unstructure_factory at ...>

>>> class MyNamedTuple(NamedTuple):
...     a: int

>>> c.unstructure(MyNamedTuple(1))
{'a': 1}
```

To only un/structure _some_ named tuples into dictionaries,
change the predicate function when registering the hook factory:

```{doctest} namedtuples
    :options: +ELLIPSIS

>>> c.register_unstructure_hook_factory(
...     lambda t: t is MyNamedTuple,
...     namedtuple_dict_unstructure_factory,
... )
<function namedtuple_dict_unstructure_factory at ...>
```

```{versionadded} 24.1.0

```
