# History

## 23.2.2 (2023-11-21)

- Fix a regression when unstructuring `Any | None`.
  ([#453](https://github.com/python-attrs/cattrs/issues/453))

## 23.2.1 (2023-11-18)

- Fix unnecessary `typing_extensions` import on Python 3.11.
  ([#446](https://github.com/python-attrs/cattrs/issues/446) [#447](https://github.com/python-attrs/cattrs/pull/447))

## 23.2.0 (2023-11-17)

- **Potentially breaking**: skip _attrs_ fields marked as `init=False` by default. This change is potentially breaking for unstructuring.
  See [here](https://catt.rs/en/latest/customizing.html#include_init_false) for instructions on how to restore the old behavior.
  ([#40](https://github.com/python-attrs/cattrs/issues/40) [#395](https://github.com/python-attrs/cattrs/pull/395))
- **Potentially breaking**: {py:func}`cattrs.gen.make_dict_structure_fn` and {py:func}`cattrs.gen.typeddicts.make_dict_structure_fn` will use the values for the `detailed_validation` and `forbid_extra_keys` parameters from the given converter by default now.
  If you're using these functions directly, the old behavior can be restored by passing in the desired values directly.
  ([#410](https://github.com/python-attrs/cattrs/issues/410) [#411](https://github.com/python-attrs/cattrs/pull/411))
- **Potentially breaking**: The default union structuring strategy will also use fields annotated as `typing.Literal` to help guide structuring.
  See [here](https://catt.rs/en/latest/unions.html#default-union-strategy) for instructions on how to restore the old behavior.
  ([#391](https://github.com/python-attrs/cattrs/pull/391))
- Python 3.12 is now supported. Python 3.7 is no longer supported; use older releases there.
  ([#424](https://github.com/python-attrs/cattrs/pull/424))
- Implement the `union passthrough` strategy, enabling much richer union handling for preconfigured converters. [Learn more here](https://catt.rs/en/stable/strategies.html#union-passthrough).
- Introduce the `use_class_methods` strategy. Learn more [here](https://catt.rs/en/latest/strategies.html#using-class-specific-structure-and-unstructure-methods).
  ([#405](https://github.com/python-attrs/cattrs/pull/405))
- The `omit` parameter of {py:func}`cattrs.override` is now of type `bool | None` (from `bool`).
  `None` is the new default and means to apply default _cattrs_ handling to the attribute, which is to omit the attribute if it's marked as `init=False`, and keep it otherwise.
- Converters can now be initialized with [custom fallback hook factories](https://catt.rs/en/latest/converters.html#fallback-hook-factories) for un/structuring.
  ([#331](https://github.com/python-attrs/cattrs/issues/311) [#441](https://github.com/python-attrs/cattrs/pull/441))
- Add support for `date` to preconfigured converters.
  ([#420](https://github.com/python-attrs/cattrs/pull/420))
- Add support for `datetime.date`s to the PyYAML preconfigured converter.
  ([#393](https://github.com/python-attrs/cattrs/issues/393))
- Fix {py:func}`format_exception() <cattrs.v.format_exception>` parameter working for recursive calls to {py:func}`transform_error <cattrs.transform_error>`.
  ([#389](https://github.com/python-attrs/cattrs/issues/389))
- [_attrs_ aliases](https://www.attrs.org/en/stable/init.html#private-attributes-and-aliases) are now supported, although aliased fields still map to their attribute name instead of their alias by default when un/structuring.
  ([#322](https://github.com/python-attrs/cattrs/issues/322) [#391](https://github.com/python-attrs/cattrs/pull/391))
- Fix TypedDicts with periods in their field names.
  ([#376](https://github.com/python-attrs/cattrs/issues/376) [#377](https://github.com/python-attrs/cattrs/pull/377))
- Optimize and improve unstructuring of `Optional` (unions of one type and `None`).
  ([#380](https://github.com/python-attrs/cattrs/issues/380) [#381](https://github.com/python-attrs/cattrs/pull/381))
- Fix {py:func}`format_exception <cattrs.v.format_exception>` and {py:func}`transform_error <cattrs.transform_error>` type annotations.
- Improve the implementation of `cattrs._compat.is_typeddict`. The implementation is now simpler, and relies on fewer private implementation details from `typing` and typing_extensions.
  ([#384](https://github.com/python-attrs/cattrs/pull/384))
- Improve handling of TypedDicts with forward references.
- Speed up generated _attrs_ and TypedDict structuring functions by changing their signature slightly.
  ([#388](https://github.com/python-attrs/cattrs/pull/388))
- Fix copying of converters with function hooks.
  ([#398](https://github.com/python-attrs/cattrs/issues/398) [#399](https://github.com/python-attrs/cattrs/pull/399))
- Broaden {py:func}`loads' <cattrs.preconf.orjson.OrjsonConverter.loads>` type definition for the preconf orjson converter.
  ([#400](https://github.com/python-attrs/cattrs/pull/400))
- {py:class}`AttributeValidationNote <cattrs.AttributeValidationNote>` and {py:class}`IterableValidationNote <cattrs.IterableValidationNote>` are now picklable.
  ([#408](https://github.com/python-attrs/cattrs/pull/408))
- Fix structuring `Final` lists.
  ([#412](https://github.com/python-attrs/cattrs/issues/412))
- Fix certain cases of structuring `Annotated` types.
  ([#418](https://github.com/python-attrs/cattrs/issues/418))
- Fix the [tagged union strategy](https://catt.rs/en/stable/strategies.html#tagged-unions-strategy) to work with `forbid_extra_keys`.
  ([#402](https://github.com/python-attrs/cattrs/issues/402) [#443](https://github.com/python-attrs/cattrs/pull/443))
- Use [PDM](https://pdm.fming.dev/latest/) instead of Poetry.
- _cattrs_ is now linted with [Ruff](https://beta.ruff.rs/docs/).
- Remove some unused lines in the unstructuring code.
  ([#416](https://github.com/python-attrs/cattrs/pull/416))
- Fix handling classes inheriting from non-generic protocols.
  ([#374](https://github.com/python-attrs/cattrs/issues/374) [#436](https://github.com/python-attrs/cattrs/pull/436))
- The documentation Makefile now supports the `htmlview` and `htmllive` targets. ([#442](https://github.com/python-attrs/cattrs/pull/442))
- _cattrs_ is now published using PyPI Trusted Publishers, and `main` branch commits are automatically deployed to Test PyPI.

## 23.1.2 (2023-06-02)

- Improve `typing_extensions` version bound. ([#372](https://github.com/python-attrs/cattrs/issues/372))

## 23.1.1 (2023-05-30)

- Add `typing_extensions` as a direct dependency on 3.10.
  ([#369](https://github.com/python-attrs/cattrs/issues/369) [#370](https://github.com/python-attrs/cattrs/pull/370))

## 23.1.0 (2023-05-30)

- Introduce the [`tagged_union` strategy](https://catt.rs/en/stable/strategies.html#tagged-unions-strategy).
  ([#318](https://github.com/python-attrs/cattrs/pull/318) [#317](https://github.com/python-attrs/cattrs/issues/317))
- Introduce the `cattrs.transform_error` helper function for formatting validation exceptions. ([258](https://github.com/python-attrs/cattrs/issues/258) [342](https://github.com/python-attrs/cattrs/pull/342))
- Add support for [`typing.TypedDict` and `typing_extensions.TypedDict`](https://peps.python.org/pep-0589/).
  ([#296](https://github.com/python-attrs/cattrs/issues/296) [#364](https://github.com/python-attrs/cattrs/pull/364))
- Add support for `typing.Final`.
  ([#340](https://github.com/python-attrs/cattrs/issues/340) [#349](https://github.com/python-attrs/cattrs/pull/349))
- Introduce `override.struct_hook` and `override.unstruct_hook`. Learn more [here](https://catt.rs/en/latest/customizing.html#struct-hook-and-unstruct-hook).
  ([#326](https://github.com/python-attrs/cattrs/pull/326))
- Fix generating structuring functions for types with angle brackets (`<>`) and pipe symbols (`|`) in the name.
  ([#319](https://github.com/python-attrs/cattrs/issues/319) [#327](https://github.com/python-attrs/cattrs/pull/327>))
- `pathlib.Path` is now supported by default.
  ([#81](https://github.com/python-attrs/cattrs/issues/81))
- Add `cbor2` serialization library to the `cattrs.preconf` package.
- Add optional dependencies for `cattrs.preconf` third-party libraries. ([#337](https://github.com/python-attrs/cattrs/pull/337))
- All preconf converters now allow overriding the default `unstruct_collection_overrides` in `make_converter`.
  ([#350](https://github.com/python-attrs/cattrs/issues/350) [#353](https://github.com/python-attrs/cattrs/pull/353))
- Subclasses structuring and unstructuring is now supported via a custom `include_subclasses` strategy.
  ([#312](https://github.com/python-attrs/cattrs/pull/312))
- Add support for `typing_extensions.Annotated` when the python version is less than `3.9`. ([#366](https://github.com/python-attrs/cattrs/pull/366))
- Add unstructuring and structuring support for the standard library `deque`.
  ([#355](https://github.com/python-attrs/cattrs/pull/355))

## 22.2.0 (2022-10-03)

- _Potentially breaking_: `cattrs.Converter` has been renamed to `cattrs.BaseConverter`, and `cattrs.GenConverter` to `cattrs.Converter`.
  The `GenConverter` name is still available for backwards compatibility, but is deprecated.
  If you were depending on functionality specific to the old `Converter`, change your import to `from cattrs import BaseConverter`.
- [NewTypes](https://docs.python.org/3/library/typing.html#newtype) are now supported by the `cattrs.Converter`.
  ([#255](https://github.com/python-attrs/cattrs/pull/255) [#94](https://github.com/python-attrs/cattrs/issues/94) [#297](https://github.com/python-attrs/cattrs/issues/297))
- `cattrs.Converter` and `cattrs.BaseConverter` can now copy themselves using the `copy` method.
  ([#284](https://github.com/python-attrs/cattrs/pull/284))
- Python 3.11 support.
- cattrs now supports un/structuring `kw_only` fields on attrs classes into/from dictionaries.
  ([#247](https://github.com/python-attrs/cattrs/pull/247))
- PyPy support (and tests, using a minimal Hypothesis profile) restored.
  ([#253](https://github.com/python-attrs/cattrs/issues/253))
- Fix propagating the `detailed_validation` flag to mapping and counter structuring generators.
- Fix `typing.Set` applying too broadly when used with the `GenConverter.unstruct_collection_overrides` parameter on Python versions below 3.9. Switch to `typing.AbstractSet` on those versions to restore the old behavior.
  ([#264](https://github.com/python-attrs/cattrs/issues/264))
- Uncap the required Python version, to avoid problems detailed [here](https://iscinumpy.dev/post/bound-version-constraints/#pinning-the-python-version-is-special)
  ([#275](https://github.com/python-attrs/cattrs/issues/275))
- Fix `Converter.register_structure_hook_factory` and `cattrs.gen.make_dict_unstructure_fn` type annotations.
  ([#281](https://github.com/python-attrs/cattrs/issues/281))
- Expose all error classes in the `cattr.errors` namespace. Note that it is deprecated, just use `cattrs.errors`.
  ([#252](https://github.com/python-attrs/cattrs/issues/252))
- Fix generating structuring functions for types with quotes in the name.
  ([#291](https://github.com/python-attrs/cattrs/issues/291) [#277](https://github.com/python-attrs/cattrs/issues/277))
- Fix usage of notes for the final version of [PEP 678](https://peps.python.org/pep-0678/), supported since `exceptiongroup>=1.0.0rc4`.
  ([#303](https://github.com/python-attrs/cattrs/pull/303))

## 22.1.0 (2022-04-03)

- _cattrs_ now uses the CalVer versioning convention.
- _cattrs_ now has a detailed validation mode, which is enabled by default. Learn more [here](https://cattrs.readthedocs.io/en/latest/validation.html).
  The old behavior can be restored by creating the converter with `detailed_validation=False`.
- _attrs_ and dataclass structuring is now ~25% faster.
- Fix an issue structuring bare `typing.List` s on Pythons lower than 3.9.
  ([#209](https://github.com/python-attrs/cattrs/issues/209))
- Fix structuring of non-parametrized containers like `list/dict/...` on Pythons lower than 3.9.
  ([#218](https://github.com/python-attrs/cattrs/issues/218))
- Fix structuring bare `typing.Tuple` on Pythons lower than 3.9.
  ([#218](https://github.com/python-attrs/cattrs/issues/218))
- Fix a wrong `AttributeError` of an missing `__parameters__` attribute. This could happen
  when inheriting certain generic classes – for example `typing.*` classes are affected.
  ([#217](https://github.com/python-attrs/cattrs/issues/217))
- Fix structuring of `enum.Enum` instances in `typing.Literal` types.
  ([#231](https://github.com/python-attrs/cattrs/pull/231))
- Fix unstructuring all tuples - unannotated, variable-length, homogenous and heterogenous - to `list`.
  ([#226](https://github.com/python-attrs/cattrs/issues/226))
- For `forbid_extra_keys` raise custom `ForbiddenExtraKeyError` instead of generic `Exception`.
  ([#225](https://github.com/python-attrs/cattrs/pull/225))
- All preconf converters now support `loads` and `dumps` directly. See an example [here](https://cattrs.readthedocs.io/en/latest/preconf.html).
- Fix mappings with byte keys for the orjson, bson and tomlkit converters.
  ([#241](https://github.com/python-attrs/cattrs/issues/241))

## 1.10.0 (2022-01-04)

- Add PEP 563 (string annotations) support for dataclasses.
  ([#195](https://github.com/python-attrs/cattrs/issues/195))
- Fix handling of dictionaries with string Enum keys for bson, orjson, and tomlkit.
- Rename the `cattr.gen.make_dict_unstructure_fn.omit_if_default` parameter to `_cattrs_omit_if_default`, for consistency. The `omit_if_default` parameters to `GenConverter` and `override` are unchanged.
- Following the changes in _attrs_ 21.3.0, add a `cattrs` package mirroring the existing `cattr` package. Both package names may be used as desired, and the `cattr` package isn't going away.

## 1.9.0 (2021-12-06)

- Python 3.10 support, including support for the new union syntax (`A | B` vs `Union[A, B]`).
- The `GenConverter` can now properly structure generic classes with generic collection fields.
  ([#149](https://github.com/python-attrs/cattrs/issues/149))
- `omit=True` now also affects generated structuring functions.
  ([#166](https://github.com/python-attrs/cattrs/issues/166))
- `cattr.gen.{make_dict_structure_fn, make_dict_unstructure_fn}` now resolve type annotations automatically when PEP 563 is used.
  ([#169](https://github.com/python-attrs/cattrs/issues/169))
- Protocols are now unstructured as their runtime types.
  ([#177](https://github.com/python-attrs/cattrs/pull/177))
- Fix an issue generating structuring functions with renaming and `_cattrs_forbid_extra_keys=True`.
  ([#190](https://github.com/python-attrs/cattrs/issues/190))

## 1.8.0 (2021-08-13)

- Fix `GenConverter` mapping structuring for unannotated dicts on Python 3.8.
  ([#151](https://github.com/python-attrs/cattrs/issues/151))
- The source code for generated un/structuring functions is stored in the `linecache` cache, which enables more informative stack traces when un/structuring errors happen using the `GenConverter`. This behavior can optionally be disabled to save memory.
- Support using the attr converter callback during structure.
  By default, this is a method of last resort, but it can be elevated to the default by setting `prefer_attrib_converters=True` on `Converter` or `GenConverter`.
  ([#138](https://github.com/python-attrs/cattrs/issues/138))
- Fix structuring recursive classes.
  ([#159](https://github.com/python-attrs/cattrs/issues/159))
- Converters now support un/structuring hook factories. This is the most powerful and complex venue for customizing un/structuring. This had previously been an internal feature.
- The [Common Usage Examples](https://cattrs.readthedocs.io/en/latest/usage.html#using-factory-hooks) documentation page now has a section on advanced hook factory usage.
- `cattr.override` now supports the `omit` parameter, which makes _cattrs_ skip the atribute entirely when unstructuring.
- The `cattr.preconf.bson` module is now tested against the `bson` module bundled with the `pymongo` package, because that package is much more popular than the standalone PyPI `bson` package.

## 1.7.1 (2021-05-28)

- `Literal` s are not supported on Python 3.9.0 (supported on 3.9.1 and later), so we skip importing them there.
  ([#150](https://github.com/python-attrs/cattrs/issues/150))

## 1.7.0 (2021-05-26)

- `cattr.global_converter` (which provides `cattr.unstructure`, `cattr.structure` etc.) is now an instance of `cattr.GenConverter`.
- `Literal` s are now supported and validated when structuring.
- Fix dependency metadata information for _attrs_.
  ([#147](https://github.com/python-attrs/cattrs/issues/147))
- Fix `GenConverter` mapping structuring for unannotated dicts.
  ([#148](https://github.com/python-attrs/cattrs/issues/148))

## 1.6.0 (2021-04-28)

- _cattrs_ now uses Poetry.
- `GenConverter` mapping structuring is now ~25% faster, and unstructuring heterogenous tuples is significantly faster.
- Add `cattr.preconf`. This package contains modules for making converters for particular serialization libraries. We currently support the standard library `json`, and third-party `ujson`, `orjson`, `msgpack`, `bson`, `pyyaml` and `tomlkit` libraries.

## 1.5.0 (2021-04-15)

- Fix an issue with `GenConverter` unstructuring _attrs_ classes and dataclasses with generic fields.
  ([#65](https://github.com/python-attrs/cattrs/issues/65))
- `GenConverter` has support for easy overriding of collection unstructuring types (for example, unstructure all sets to lists) through its `unstruct_collection_overrides` argument.
  ([#137](https://github.com/python-attrs/cattrs/pull/137))
- Unstructuring mappings with `GenConverter` is significantly faster.
- `GenConverter` supports strict handling of unexpected dictionary keys through its `forbid_extra_keys` argument.
  ([#142](https://github.com/python-attrs/cattrs/pull/142))

## 1.4.0 (2021-03-21)

- Fix an issue with `GenConverter` un/structuring hooks when a function hook is registered after the converter has already been used.
- Add support for `collections.abc.{Sequence, MutableSequence, Set, MutableSet}`. These should be used on 3.9+ instead of their `typing` alternatives, which are deprecated.
  ([#128](https://github.com/python-attrs/cattrs/issues/128))
- The `GenConverter` will unstructure iterables (`list[T]`, `tuple[T, ...]`, `set[T]`) using their type argument instead of the runtime class if its elements, if possible. These unstructuring operations are up to 40% faster.
  ([#129](https://github.com/python-attrs/cattrs/issues/129))
- Flesh out `Converter` and `GenConverter` initializer type annotations.
  ([#131](https://github.com/python-attrs/cattrs/issues/131))
- Add support for `typing.Annotated` on Python 3.9+. _cattrs_ will use the first annotation present. _cattrs_ specific annotations may be added in the future.
  ([#127](https://github.com/python-attrs/cattrs/issues/127))
- Add support for dataclasses.
  ([#43](https://github.com/python-attrs/cattrs/issues/43))

## 1.3.0 (2021-02-25)

- _cattrs_ now has a benchmark suite to help make and keep cattrs the fastest it can be. The instructions on using it can be found under the [Benchmarking](https://cattrs.readthedocs.io/en/latest/benchmarking.html) section in the docs.
  ([#123](https://github.com/python-attrs/cattrs/pull/123))
- Fix an issue unstructuring tuples of non-primitives.
  ([#125](https://github.com/python-attrs/cattrs/issues/125))
- _cattrs_ now calls `attr.resolve_types` on _attrs_ classes when registering un/structuring hooks.
- `GenConverter` structuring and unstructuring of _attrs_ classes is significantly faster.

## 1.2.0 (2021-01-31)

- `converter.unstructure` now supports an optional parameter, `unstructure_as`, which can be used to unstructure something as a different type. Useful for unions.
- Improve support for union un/structuring hooks. Flesh out docs for advanced union handling.
  ([#115](https://github.com/python-attrs/cattrs/pull/115))
- Fix `GenConverter` behavior with inheritance hierarchies of _attrs_ classes.
  ([#117](https://github.com/python-attrs/cattrs/pull/117 [#116](https://github.com/python-attrs/cattrs/issues/116>))
- Refactor `GenConverter.un/structure_attrs_fromdict` into `GenConverter.gen_un/structure_attrs_fromdict` to allow calling back to `Converter.un/structure_attrs_fromdict` without sideeffects.
  ([#118](https://github.com/python-attrs/cattrs/issues/118))

## 1.1.2 (2020-11-29)

- The default disambiguator will not consider non-required fields any more.
  ([#108](https://github.com/python-attrs/cattrs/pull/108))
- Fix a couple type annotations.
  ([#107](https://github.com/python-attrs/cattrs/pull/107) [#105](https://github.com/python-attrs/cattrs/issues/105))
- Fix a `GenConverter` unstructuring issue and tests.

## 1.1.1 (2020-10-30)

- Add metadata for supported Python versions.
  ([#103](https://github.com/python-attrs/cattrs/pull/103))

## 1.1.0 (2020-10-29)

- Python 2, 3.5 and 3.6 support removal. If you need it, use a version below 1.1.0.
- Python 3.9 support, including support for built-in generic types (`list[int]` vs `typing.List[int]`).
- _cattrs_ now includes functions to generate specialized structuring and unstructuring hooks. Specialized hooks are faster and support overrides (`omit_if_default` and `rename`). See the `cattr.gen` module.
- _cattrs_ now includes a converter variant, `cattr.GenConverter`, that automatically generates specialized hooks for attrs classes. This converter will become the default in the future.
- Generating specialized structuring hooks now invokes [attr.resolve_types](https://www.attrs.org/en/stable/api.html#attr.resolve_types) on a class if the class makes use of the new PEP 563 annotations.
- _cattrs_ now depends on _attrs_ >= 20.1.0, because of `attr.resolve_types`.
- Specialized hooks now support generic classes. The default converter will generate and use a specialized hook upon encountering a generic class.

## 1.0.0 (2019-12-27)

- _attrs_ classes with private attributes can now be structured by default.
- Structuring from dictionaries is now more lenient: extra keys are ignored.
- _cattrs_ has improved type annotations for use with Mypy.
- Unstructuring sets and frozensets now works properly.

## 0.9.1 (2019-10-26)

- Python 3.8 support.

## 0.9.0 (2018-07-22)

- Python 3.7 support.

## 0.8.1 (2018-06-19)

- The disambiguation function generator now supports unions of _attrs_ classes and NoneType.

## 0.8.0 (2018-04-14)

- Distribution fix.

## 0.7.0 (2018-04-12)

- Removed the undocumented `Converter.unstruct_strat` property setter.
- Removed the ability to set the `Converter.structure_attrs` instance field.
- Some micro-optimizations were applied; a `structure(unstructure(obj))` roundtrip
  is now up to 2 times faster.

## 0.6.0 (2017-12-25)

- Packaging fixes.
  ([#17](https://github.com/python-attrs/cattrs/pull/17))

## 0.5.0 (2017-12-11)

- structure/unstructure now supports using functions as well as classes for deciding the appropriate function.
- added `Converter.register_structure_hook_func`, to register a function instead of a class for determining handler func.
- added `Converter.register_unstructure_hook_func`, to register a function instead of a class for determining handler func.
- vendored typing is no longer needed, nor provided.
- Attributes with default values can now be structured if they are missing in the input.
  ([#15](https://github.com/python-attrs/cattrs/pull/15))
- `Optional` attributes can no longer be structured if they are missing in the input.
- `cattr.typed` removed since the functionality is now present in _attrs_ itself.
  Replace instances of `cattr.typed(type)` with `attr.ib(type=type)`.

## 0.4.0 (2017-07-17)

- `Converter.loads` is now `Converter.structure`, and `Converter.dumps` is now `Converter.unstructure`.
- Python 2.7 is supported.
- Moved `cattr.typing` to `cattr.vendor.typing` to support different vendored versions of typing.py for Python 2 and Python 3.
- Type metadata can be added to _attrs_ classes using `cattr.typed`.

## 0.3.0 (2017-03-18)

- Python 3.4 is no longer supported.
- Introduced `cattr.typing` for use with Python versions 3.5.2 and 3.6.0.
- Minor changes to work with newer versions of `typing`.
- Bare Optionals are not supported any more (use `Optional[Any]`).
- Attempting to load unrecognized classes will result in a ValueError, and a helpful message to register a loads hook.
- Loading _attrs_ classes is now documented.
- The global converter is now documented.
- `cattr.loads_attrs_fromtuple` and `cattr.loads_attrs_fromdict` are now exposed.

## 0.2.0 (2016-10-02)

- Tests and documentation.

## 0.1.0 (2016-08-13)

- First release on PyPI.
