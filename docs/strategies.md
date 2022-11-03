# Strategies

_cattrs_ ships with a number of _strategies_ for customizing un/structuring behavior.

Strategies are prepackaged, high-level patterns for quickly and easily applying complex customizations to a converter.

## Tagged Unions

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

By default, the tag field name is `_type` and the tag value is the `__name__` of the union member.
Both the field name and value can be overriden.
The union members aren't required to be attrs classes or dataclasses, although those work automatically.
They may be anything that cattrs can un/structure from/to a dictionary, like a type with registered custom hooks.

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

The Apple App Store supports [server callbacks](https://developer.apple.com/documentation/appstoreservernotifications), in which Apple sends a JSON payload to a URL of your choosing.
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
>>> configure_tagged_union(AppleNotification, c, tag_name="notificationType", tag_generator={Refund: "REFUND"}, default=OtherAppleNotification)

```
