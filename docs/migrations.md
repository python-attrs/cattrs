# Migrations

```{currentmodule} cattrs
```

_cattrs_ sometimes changes in backwards-incompatible ways.
This page contains guidance for changes and workarounds for restoring legacy behavior.

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
