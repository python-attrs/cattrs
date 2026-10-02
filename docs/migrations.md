# Migrations

```{currentmodule} cattrs
```

_cattrs_ sometimes changes in backwards-incompatible ways.
This page contains guidance for changes and workarounds for restoring legacy behavior.

## 26.2.0

### Naive datetimes unstructuring as UTC in the _msgpack_ and _cbor2_ converters

The _msgpack_ and _cbor2_ converters unstructure `datetime` s into UNIX timestamps using `datetime.timestamp`, which reads a naive `datetime` as local time.
The serialized value therefore depended on the timezone of the machine doing the unstructuring, while the structure hooks read timestamps back as UTC.
From this version on, naive `datetime` s are assumed to be UTC when unstructuring, so both ends of the round-trip agree and the payload no longer depends on the host.

Aware `datetime` s are unaffected.

The old behavior can be restored by registering `datetime.timestamp` directly on a converter.

```python
>>> from datetime import datetime

>>> converter.register_unstructure_hook(datetime, datetime.timestamp)
```

## 25.3.0

### Abstract sets structuring into frozensets

From this version on, abstract sets (`collection.abc.Set`) structure into frozensets.

The old behavior can be restored by registering the {meth}`BaseConverter._structure_set <cattrs.BaseConverter._structure_set>` method using the {meth}`is_abstract_set <cattrs.cols.is_abstract_set>` predicate on a converter.

```python
>>> from cattrs.cols import is_abstract_set

>>> converter.register_structure_hook_func(is_abstract_set, converter._structure_set)
```

## 25.2.0

### Sequences structuring into tuples

Sequences were changed to structure into tuples instead of lists.

The old behavior can be restored by registering the `list_structure_factory` using the `is_sequence` predicate on a converter.

```python
>>> from cattrs.cols import is_sequence, list_structure_factory

>>> converter.register_structure_hook_factory(is_sequence, list_structure_factory)
```

## 25.1.0

### The default structure hook fallback factory

The default structure hook fallback factory was changed to more eagerly raise errors for missing hooks.

The old behavior can be restored by explicitly passing in the old hook fallback factory when instantiating the converter.


```python
>>> from cattrs.fns import raise_error

>>> c = Converter(structure_fallback_factory=lambda _: raise_error)
# Or
>>> c = BaseConverter(structure_fallback_factory=lambda _: raise_error)
```

### `cattrs.gen.MappingStructureFn` and `cattrs.gen.DictStructureFn` removal

The internal `cattrs.gen.MappingStructureFn` and `cattrs.gen.DictStructureFn` types were replaced by a more general type, `cattrs.SimpleStructureHook[In, T]`.
If you were using `MappingStructureFn`, use `SimpleStructureHook[Mapping[Any, Any], T]` instead.
If you were using `DictStructureFn`, use `SimpleStructureHook[Mapping[str, Any], T]` instead.

## 23.2.0

(include-init-false-fields)=
### Including `init=False` fields on a converter

From this version on, _attrs_ fields declared with `init=False` are skipped by default when structuring and unstructuring.
To include these fields for multiple classes, register hook factories on a converter before generating other hooks or converting values, since generated hooks resolve nested hooks early.
The factories below generate dict hooks for each _attrs_ class encountered, including nested classes, with `_cattrs_include_init_false=True`.

```{doctest}
>>> from attrs import define, field, has
>>> from cattrs import Converter
>>> from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn
>>>
>>> @define
... class Record:
...     number: int
...     cached: int = field(init=False, default=0)
>>>
>>> @define
... class Batch:
...     record: Record
...     label: str = field(init=False, default="")
>>>
>>> batch = Batch(Record(1))
>>> batch.record.cached = 7
>>> batch.label = "ready"
>>> default_converter = Converter()
>>> default_converter.unstructure(batch)
{'record': {'number': 1}}
>>>
>>> converter = Converter()
>>> _ = converter.register_unstructure_hook_factory(
...     has,
...     lambda cls: make_dict_unstructure_fn(
...         cls, converter, _cattrs_include_init_false=True
...     ),
... )
>>> _ = converter.register_structure_hook_factory(
...     has,
...     lambda cls: make_dict_structure_fn(
...         cls, converter, _cattrs_include_init_false=True
...     ),
... )
>>> data = converter.unstructure(batch)
>>> data
{'record': {'number': 1, 'cached': 7}, 'label': 'ready'}
>>> converter.structure(data, Batch)
Batch(record=Record(number=1, cached=7), label='ready')
>>> default_converter.unstructure(batch)
{'record': {'number': 1}}
```

Register both factories to include the fields in both directions; registering only the unstructuring factory changes only the generated output.
These registrations affect this converter, not other converters or the module-level conversion functions.
The example uses mutable classes: structuring assigns `init=False` fields after constructing the instance.
Use the {ref}`per-class or per-field customization <customizing-include-init-false>` when only selected classes or fields should be included.
