# Tips for Handling Unions

This sections contains information for advanced union handling.

As mentioned in the structuring section, _cattrs_ is able to handle simple unions of _attrs_ classes automatically.
More complex cases require converter customization (since there are many ways of handling unions).

_cattrs_ also comes with a number of strategies to help handle unions:

- [tagged unions strategy](strategies.md#tagged-unions-strategy) mentioned below
- [union passthrough strategy](strategies.md#union-passthrough), which is preapplied to all the [preconfigured](preconf.md) converters

## Unstructuring unions with extra metadata

```{note}
_cattrs_ comes with the [tagged unions strategy](strategies.md#tagged-unions-strategy) for handling this exact use-case since version 23.1.
The example below has been left here for educational purposes, but you should prefer the strategy.
```

Let's assume a simple scenario of two classes, `ClassA` and `ClassB`, both
of which have no distinct fields and so cannot be used automatically with
_cattrs_.

```python
@define
class ClassA:
    a_string: str

@define
class ClassB:
    a_string: str
```

A naive approach to unstructuring either of these would yield identical
dictionaries, and not enough information to restructure the classes.

```python
>>> converter.unstructure(ClassA("test"))
{'a_string': 'test'}  # Is this ClassA or ClassB? Who knows!
```

What we can do is ensure some extra information is present in the
unstructured data, and then use that information to help structure later.

First, we register an unstructure hook for the `Union[ClassA, ClassB]` type.

```python
>>> converter.register_unstructure_hook(
...     Union[ClassA, ClassB],
...     lambda o: {"_type": type(o).__name__,  **converter.unstructure(o)}
... )
>>> converter.unstructure(ClassA("test"), unstructure_as=Union[ClassA, ClassB])
{'_type': 'ClassA', 'a_string': 'test'}
```

Note that when unstructuring, we had to provide the `unstructure_as` parameter
or _cattrs_ would have just applied the usual unstructuring rules to `ClassA`,
instead of our special union hook.

Now that the unstructured data contains some information, we can create a
structuring hook to put it to use:

```python
>>> converter.register_structure_hook(
...     Union[ClassA, ClassB],
...     lambda o, _: converter.structure(o, ClassA if o["_type"] == "ClassA" else ClassB)
... )
>>> converter.structure({"_type": "ClassA", "a_string": "test"}, Union[ClassA, ClassB])
ClassA(a_string='test')
```
