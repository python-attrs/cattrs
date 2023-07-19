# Strategies

_cattrs_ ships with a number of _strategies_ for customizing un/structuring behavior.

Strategies are prepackaged, high-level patterns for quickly and easily applying complex customizations to a converter.

## Tagged Unions Strategy

_Found at {py:func}`cattrs.strategies.configure_tagged_union`._

The _tagged union_ strategy allows for un/structuring a union of classes by including an additional field (the _tag_) in the unstructured representation.
Each tag value is associated with a member of the union.

```{doctest} tagged_unions

>>> from cattrs.strategies import configure_tagged_union
>>> from cattrs import Converter
>>> converter = Converter()

>>> @define
... class A:
...     a: int

>>> @define
... class B:
...     b: str

>>> configure_tagged_union(A | B, converter)

>>> converter.unstructure(A(1), unstructure_as=A | B)
{'a': 1, '_type': 'A'}

>>> converter.structure({'a': 1, '_type': 'A'}, A | B)
A(a=1)
```

By default, the tag field name is `_type` and the tag value is the class name of the union member.
Both the field name and value can be overriden.

The `tag_generator` parameter is a one-argument callable that will be called with every member of the union to generate a mapping of tag values to union members.
Here are some common `tag_generator` uses:

| Tag info available in         | Recommended `tag_generator`                             |
| ----------------------------- | ------------------------------------------------------- |
| Name of the class             | Use the default, or `lambda cl: cl.__name__`            |
| A class variable (`classvar`) | `lambda cl: cl.classvar`                                |
| A dictionary (`mydict`)       | `mydict.get` or `mydict.__getitem__`                    |
| An enum of possible values    | Build a dictionary of classes to enum values and use it |

The union members aren't required to be attrs classes or dataclasses, although those work automatically.
They may be anything that cattrs can un/structure from/to a dictionary, for example a type with registered custom hooks.

A default member can be specified to be used if the tag is missing or is unknown.
This is useful for evolving APIs in a backwards-compatible way; an endpoint taking class `A` can be changed to take `A | B` with `A` as the default (for old clients which do not send the tag).

This strategy only applies in the context of the union; the normal un/structuring hooks are left untouched.
This also means union members can be reused in multiple unions easily.

```{doctest} tagged_unions

# Unstructuring as a union.
>>> converter.unstructure(A(1), unstructure_as=A | B)
{'a': 1, '_type': 'A'}

# Unstructuring as just an `A`.
>>> converter.unstructure(A(1))
{'a': 1}
```

### Real-life Case Study

The Apple App Store supports [server callbacks](https://developer.apple.com/documentation/appstoreservernotifications), by which Apple sends a JSON payload to a URL of your choice.
The payload can be interpreted as about a dozen different messages, based on the value of the `notificationType` field.

To keep the example simple we define two classes, one for the `REFUND` event and one for everything else.

```python

@define
class Refund:
    originalTransactionId: str

@define
class OtherAppleNotification:
    notificationType: str

AppleNotification = Refund | OtherAppleNotification

```

Next, we use the _tagged unions_ strategy to prepare our converter.
The tag value for the `Refund` event is `REFUND`, and we can let the `OtherAppleNotification` class handle all the other cases.
The `tag_generator` parameter is a callable, so we can give it the `get` method of a dictionary.

```python

>>> c = Converter()
>>> configure_tagged_union(
...     AppleNotification,
...     c,
...     tag_name="notificationType",
...     tag_generator={Refund: "REFUND"},
...     default=OtherAppleNotification
... )

```

The converter is now ready to start structuring Apple notifications.

```python

>>> payload = {"notificationType": "REFUND", "originalTransactionId": "1"}
>>> notification = c.structure(payload, AppleNotification)

>>> match notification:
...     case Refund(txn_id):
...         print(f"Refund for {txn_id}!")
...     case OtherAppleNotification(not_type):
...         print("Can't handle this yet")

```

```{versionadded} 23.1.0

```

## Include Subclasses Strategy

_Found at {py:func}`cattrs.strategies.include_subclasses`._

The _include subclass_ strategy allows the un/structuring of a base class to an instance of itself or one of its descendants.
Conceptually with this strategy, each time an un/structure operation for the base class is asked, `cattrs` machinery replaces that operation as if the union of the base class and its descendants had been asked instead.

```{doctest} include_subclass

>>> from attrs import define
>>> from cattrs.strategies import include_subclasses
>>> from cattrs import Converter

>>> @define
... class Parent:
...     a: int

>>> @define
... class Child(Parent):
...     b: str

>>> converter = Converter()
>>> include_subclasses(Parent, converter)

>>> converter.unstructure(Child(a=1, b="foo"), unstructure_as=Parent)
{'a': 1, 'b': 'foo'}

>>> converter.structure({'a': 1, 'b': 'foo'}, Parent)
Child(a=1, b='foo')
```

In the example above, we asked to unstructure then structure a `Child` instance as the `Parent` class and in both cases we correctly obtained back the unstructured and structured versions of the `Child` instance.
If we did not apply the `include_subclasses` strategy, this is what we would have obtained:

```python
>>> converter_no_subclasses = Converter()

>>> converter_no_subclasses.unstructure(Child(a=1, b="foo"), unstructure_as=Parent)
{'a': 1}

>>> converter_no_subclasses.structure({'a': 1, 'b': 'foo'}, Parent)
Parent(a=1)
```

Without the application of the strategy, in both unstructure and structure operations, we received a `Parent` instance.

```{note}
The handling of subclasses is an opt-in feature for two main reasons:
- Performance. While small and probably negligeable in most cases the subclass handling incurs more function calls and has a performance impact. 
- Customization. The specific handling of subclasses can be different from one situation to the other. In particular there is not apparent universal good defaults for disambiguating the union type. Consequently the decision is left to the user.
```

```{warning}
To work properly, all subclasses must be defined when the `include_subclasses` strategy is applied to a `converter`. If subclasses types are defined later, for instance in the context of a plug-in mechanism using inheritance, then those late defined subclasses will not be part of the subclasses union type and will not be un/structured as expected.
```

### Customization

In the example shown in the previous section, the default options for `include_subclasses` work well because the `Child` class has an attribute that do not exist in the `Parent` class (the `b` attribute).
The automatic union type disambiguation function which is based on finding unique fields for each type of the union works as intended.

Sometimes, more disambiguation customization is required.
For instance, the unstructuring operation would have failed if `Child` did not have an extra attribute or if a sibling of `Child` had also a `b` attribute.
For those cases, a callable of 2 positional arguments (a union type and a converter) defining a [tagged union strategy](strategies.md#tagged-unions-strategy) can be passed to the `include_subclasses` strategy.
{py:func}`configure_tagged_union()<cattrs.strategies.configure_tagged_union>` can be used as-is, but if you want to change its defaults, the [partial](https://docs.python.org/3/library/functools.html#functools.partial) function from the `functools` module in the standard library can come in handy.

```python

>>> from functools import partial
>>> from attrs import define
>>> from cattrs.strategies import include_subclasses, configure_tagged_union
>>> from cattrs import Converter

>>> @define
... class Parent:
...     a: int

>>> @define
... class Child1(Parent):
...     b: str

>>> @define
... class Child2(Parent):
...     b: int

>>> converter = Converter()
>>> union_strategy = partial(configure_tagged_union, tag_name="type_name")
>>> include_subclasses(Parent, converter, union_strategy=union_strategy)

>>> converter.unstructure(Child1(a=1, b="foo"), unstructure_as=Parent)
{'a': 1, 'b': 'foo', 'type_name': 'Child1'}

>>> converter.structure({'a': 1, 'b': 1, 'type_name': 'Child2'}, Parent)
Child2(a=1, b=1)
```

Other customizations available see are (see {py:func}`include_subclasses()<cattrs.strategies.include_subclasses>`):
- The exact list of subclasses that should participate to the union with the `subclasses` argument.
- Attribute overrides that permit the customization of attributes un/structuring like renaming an attribute.

Here is an example involving both customizations:

```python

>>> from attrs import define
>>> from cattrs.strategies import include_subclasses
>>> from cattrs import Converter, override

>>> @define
... class Parent:
...     a: int

>>> @define
... class Child(Parent):
...     b: str

>>> converter = Converter()
>>> include_subclasses(
...     Parent,
...     converter,
...     subclasses=(Parent, Child),
...     overrides={"b": override(rename="c")}
... )

>>> converter.unstructure(Child(a=1, b="foo"), unstructure_as=Parent)
{'a': 1, 'c': 'foo'}

>>> converter.structure({'a': 1, 'c': 'foo'}, Parent)
Child(a=1, b='foo')
```

```{versionadded} 23.1.0

```

### Using Dedicated Structure and Unstructure Methods

The following strategy can be applied to both structuring and unstructuring (also simultaneously), but for
simplicity sake, only structuring is described here.

If a class requires special handling for structuring, you can add a dedicated structuring method:

```python
>>> from attrs import define
>>> from cattrs import Converter

>>> @define
... class MyClass:
...     a: int

>>> @classmethod
... def structure(cls, data: dict):
...     return cls(data["b"])  # Not a

>>> c = Converter()
>>> c.register_structure_hook_func(lambda t: hasattr(t, "structure"), lambda v, t: t.structure(v))

>>> print(c.structure({"b": 1}, MyClass))  # the input dictionary uses "b", but 'structure()' will take care of that
MyClass(a=1)
```

The {py:func}`register_structure_hook_func()<cattrs.converters.BaseConverter.register_structure_hook_func>`
function checks the availability of a `structure` method (feel free to pick a different name).
Only if available, this method is used for structuring the given data into the target class.
Any other class without a `structure` method will use the default strategy for structuring.
