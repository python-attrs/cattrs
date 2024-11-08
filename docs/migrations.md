# Migrations

_cattrs_ sometimes changes in backwards-incompatible ways.
This page contains guidance for changes and workarounds for restoring legacy behavior.

## 24.2.0

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