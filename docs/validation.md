# Validation

_cattrs_ supports _structuring_ since its initial release, and _validation_ since release 24.1.

**Structuring** is the process of ensuring data matches a set of Python types;
it can be thought of as validating data against structural constraints.
Structuring ensures the shape of your data.
Structuring ensures data typed as `list[int]` really contains a list of integers.

**Validation** is the process of ensuring data matches a set of user-provided constraints;
it can be thought of as validating the value of data.
Validation happens after the shape of the data has been ensured.
Validation can ensure a `list[int]` contains at least one integer, and that all integers are positive.

## (Value) Validation

```{versionadded} 24.1.0

```
```{note} _This API is still provisional; as such it is subject to breaking changes._

```

_cattrs_ can be configured to validate the values of your data (ensuring a list of integers has at least one member, and that all elements are positive).

The basic unit of value validation is a function that takes a value and, if the value is unacceptable, either raises an exception or returns exactly `False`.
These functions are called _validators_.

The attributes of _attrs_ classes can be validated with the use of a helper function, {func}`cattrs.v.customize`, and a helper class, {class}`cattrs.v.V`.
_V_ is the validation attribute, mapping to _attrs_ or _dataclass_ attributes.

```python
from attrs import define
from cattrs import Converter
from cattrs.v import customize, V

@define
class C:
    a: int

converter = Converter()

customize(converter, C, V("a").ensure(lambda a: a > 0))
```

Now, every structuring of class `C` will run the provided validator(s).

```python
converter.structure({"a": -1}, C)
```

This process also works with dataclasses:

```python
from dataclasses import dataclass

@dataclass
class D:
    a: int

customize(converter, D, V("a").ensure(lambda a: a == 5))
```

## Detailed Validation

```{versionadded} 22.1.0

```
Detailed validation is enabled by default and can be disabled for a speed boost by creating a converter with `detailed_validation=False`.
When running under detailed validation, the structuring hooks are slightly slower but produce richer and more precise error messages.
Unstructuring hooks are not affected.

In detailed validation mode, any structuring errors will be grouped and raised together as a {class}`cattrs.BaseValidationError`, which is a [PEP 654 ExceptionGroup](https://www.python.org/dev/peps/pep-0654/).
ExceptionGroups are special exceptions which contain lists of other exceptions, which may themselves be other ExceptionGroups.
In essence, ExceptionGroups are trees of exceptions.

When structuring a class, _cattrs_ will gather any exceptions on a field-by-field basis and raise them as a {class}`cattrs.ClassValidationError`, which is a subclass of {class}`BaseValidationError <cattrs.BaseValidationError>`.

When structuring sequences and mappings, _cattrs_ will gather any exceptions on a key- or index-basis and raise them as a {class}`cattrs.IterableValidationError`, which is a subclass of {class}`BaseValidationError <cattrs.BaseValidationError>`.

The exceptions will also have their `__notes__` attributes set, as per [PEP 678](https://www.python.org/dev/peps/pep-0678/), showing the field, key or index for each inner exception.

A simple example involving a class containing a list and a dictionary:

```python
@define
class Class:
    a_list: list[int]
    a_dict: dict[str, int]

>>> structure({"a_list": ["a"], "a_dict": {"str": "a"}}, Class)
  + Exception Group Traceback (most recent call last):
  |   File "<stdin>", line 1, in <module>
  |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 276, in structure
  |     return self._structure_func.dispatch(cl)(obj, cl)
  |   File "<cattrs generated structure __main__.Class>", line 14, in structure_Class
  |     if errors: raise __c_cve('While structuring Class', errors, __cl)
  | cattrs.errors.ClassValidationError: While structuring Class
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "<cattrs generated structure __main__.Class>", line 5, in structure_Class
    |     res['a_list'] = __c_structure_a_list(o['a_list'], __c_type_a_list)
    |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 457, in _structure_list
    |     raise IterableValidationError(
    | cattrs.errors.IterableValidationError: While structuring list[int]
    | Structuring class Class @ attribute a_list
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 450, in _structure_list
      |     res.append(handler(e, elem_type))
      |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 375, in _structure_call
      |     return cl(obj)
      | ValueError: invalid literal for int() with base 10: 'a'
      | Structuring list[int] @ index 0
      +------------------------------------
    +---------------- 2 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "<cattrs generated structure __main__.Class>", line 10, in structure_Class
    |     res['a_dict'] = __c_structure_a_dict(o['a_dict'], __c_type_a_dict)
    |   File "", line 17, in structure_mapping
    | cattrs.errors.IterableValidationError: While structuring dict
    | Structuring class Class @ attribute a_dict
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "", line 5, in structure_mapping
      | ValueError: invalid literal for int() with base 10: 'a'
      | Structuring mapping value @ key 'str'
      +------------------------------------
```

### Transforming Exceptions into Error Messages

```{versionadded} 23.1.0

```

ExceptionGroup stack traces are useful while developing, but sometimes a more compact representation of validation errors is required.
_cattrs_ provides a helper function, {func}`cattrs.transform_error`, which transforms validation errors into lists of error messages.

The example from the previous paragraph produces the following error messages:

```{testsetup} class
@define
class Class:
    a_list: list[int]
    a_dict: dict[str, int]
```

```{doctest} class

>>> from cattrs import structure, transform_error

>>> try:
...     structure({"a_list": ["a"], "a_dict": {"str": "a"}}, Class)
... except Exception as exc:
...     print(transform_error(exc))
['invalid value for type, expected int @ $.a_list[0]', "invalid value for type, expected int @ $.a_dict['str']"]
```

A small number of built-in exceptions are converted into error messages automatically.
This can be further customized by providing {func}`cattrs.transform_error` with a function that it can use to turn individual, non-ExceptionGroup exceptions into error messages.
A useful pattern is wrapping the default, {func}`cattrs.v.format_exception` function.

```
>>> from cattrs.v import format_exception

>>> def my_exception_formatter(exc: BaseException, type) -> str:
...     if isinstance(exc, MyInterestingException):
...         return "My error message"
...     return format_exception(exc, type)

>>> try:
...     structure(..., Class)
... except Exception as exc:
...     print(transform_error(exc, format_exception=my_exception_formatter))
```

If even more customization is required, {func}`cattrs.transform_error` can be copied over into your codebase and adjusted as needed.

## Non-detailed Validation

Non-detailed validation can be enabled by initializing any of the converters with `detailed_validation=False`.
In this mode, any errors during un/structuring will bubble up directly as soon as they happen.
