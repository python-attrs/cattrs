=======
History
=======
1.10.0 (UNRELEASED)
-------------------
* Add PEP 563 (string annotations) support for dataclasses.
  (`#195 <https://github.com/python-attrs/cattrs/issues/195>`_)
* Fix handling of dictionaries with string Enum keys for bson, orjson, and tomlkit.
* Rename the ``cattr.gen.make_dict_unstructure_fn.omit_if_default`` parameter to ``_cattrs_omit_if_default``, for consistency. The ``omit_if_default`` parameters to ``GenConverter`` and ``override`` are unchanged.
* Following the changes in ``attrs`` 21.3.0, add a ``cattrs`` package mirroring the existing ``cattr`` package. Both package names may be used as desired, and the ``cattr`` package isn't going away.

1.9.0 (2021-12-06)
------------------
* Python 3.10 support, including support for the new union syntax (``A | B`` vs ``Union[A, B]``).
* The ``GenConverter`` can now properly structure generic classes with generic collection fields.
  (`#149 <https://github.com/python-attrs/cattrs/issues/149>`_)
* ``omit=True`` now also affects generated structuring functions.
  (`#166 <https://github.com/python-attrs/cattrs/issues/166>`_)
* `cattr.gen.{make_dict_structure_fn, make_dict_unstructure_fn}` now resolve type annotations automatically when PEP 563 is used.
  (`#169 <https://github.com/python-attrs/cattrs/issues/169>`_)
* Protocols are now unstructured as their runtime types.
  (`#177 <https://github.com/python-attrs/cattrs/pull/177>`_)
* Fix an issue generating structuring functions with renaming and `_cattrs_forbid_extra_keys=True`.
  (`#190 <https://github.com/python-attrs/cattrs/issues/190>`_)

1.8.0 (2021-08-13)
------------------
* Fix ``GenConverter`` mapping structuring for unannotated dicts on Python 3.8.
  (`#151 <https://github.com/python-attrs/cattrs/issues/151>`_)
* The source code for generated un/structuring functions is stored in the `linecache` cache, which enables more informative stack traces when un/structuring errors happen using the `GenConverter`. This behavior can optionally be disabled to save memory.
* Support using the attr converter callback during structure.
  By default, this is a method of last resort, but it can be elevated to the default by setting `prefer_attrib_converters=True` on `Converter` or `GenConverter`.
  (`#138 <https://github.com/python-attrs/cattrs/issues/138>`_)
* Fix structuring recursive classes.
  (`#159 <https://github.com/python-attrs/cattrs/issues/159>`_)
* Converters now support un/structuring hook factories. This is the most powerful and complex venue for customizing un/structuring. This had previously been an internal feature.
* The `Common Usage Examples <https://cattrs.readthedocs.io/en/latest/usage.html#using-factory-hooks>`_ documentation page now has a section on advanced hook factory usage.
* ``cattr.override`` now supports the ``omit`` parameter, which makes ``cattrs`` skip the atribute entirely when unstructuring.
* The ``cattr.preconf.bson`` module is now tested against the ``bson`` module bundled with the ``pymongo`` package, because that package is much more popular than the standalone PyPI ``bson`` package.

1.7.1 (2021-05-28)
------------------
* ``Literal`` s are not supported on Python 3.9.0 (supported on 3.9.1 and later), so we skip importing them there.
  (`#150 <https://github.com/python-attrs/cattrs/issues/150>`_)

1.7.0 (2021-05-26)
------------------
* ``cattr.global_converter`` (which provides ``cattr.unstructure``, ``cattr.structure`` etc.) is now an instance of ``cattr.GenConverter``.
* ``Literal`` s are now supported and validated when structuring.
* Fix dependency metadata information for ``attrs``.
  (`#147 <https://github.com/python-attrs/cattrs/issues/147>`_)
* Fix ``GenConverter`` mapping structuring for unannotated dicts.
  (`#148 <https://github.com/python-attrs/cattrs/issues/148>`_)

1.6.0 (2021-04-28)
------------------
* ``cattrs`` now uses Poetry.
* ``GenConverter`` mapping structuring is now ~25% faster, and unstructuring heterogenous tuples is significantly faster.
* Add ``cattr.preconf``. This package contains modules for making converters for particular serialization libraries. We currently support the standard library ``json``, and third-party ``ujson``, ``orjson``, ``msgpack``, ``bson``, ``pyyaml`` and ``tomlkit`` libraries.

1.5.0 (2021-04-15)
------------------
* Fix an issue with ``GenConverter`` unstructuring ``attrs`` classes and dataclasses with generic fields.
  (`#65 <https://github.com/python-attrs/cattrs/issues/65>`_)
* ``GenConverter`` has support for easy overriding of collection unstructuring types (for example, unstructure all sets to lists) through its ``unstruct_collection_overrides`` argument.
  (`#137 <https://github.com/python-attrs/cattrs/pull/137>`_)
* Unstructuring mappings with ``GenConverter`` is significantly faster.
* ``GenConverter`` supports strict handling of unexpected dictionary keys through its ``forbid_extra_keys`` argument.
  (`#142 <https://github.com/python-attrs/cattrs/pull/142>`_)

1.4.0 (2021-03-21)
------------------
* Fix an issue with ``GenConverter`` un/structuring hooks when a function hook is registered after the converter has already been used.
* Add support for ``collections.abc.{Sequence, MutableSequence, Set, MutableSet}``. These should be used on 3.9+ instead of their ``typing`` alternatives, which are deprecated.
  (`#128 <https://github.com/python-attrs/cattrs/issues/128>`_)
* The ``GenConverter`` will unstructure iterables (``list[T]``, ``tuple[T, ...]``, ``set[T]``) using their type argument instead of the runtime class if its elements, if possible. These unstructuring operations are up to 40% faster.
  (`#129 <https://github.com/python-attrs/cattrs/issues/129>`_)
* Flesh out ``Converter`` and ``GenConverter`` initializer type annotations.
  (`#131 <https://github.com/python-attrs/cattrs/issues/131>`_)
* Add support for ``typing.Annotated`` on Python 3.9+. ``cattrs`` will use the first annotation present. ``cattrs`` specific annotations may be added in the future.
  (`#127 <https://github.com/python-attrs/cattrs/issues/127>`_)
* Add support for dataclasses.
  (`#43 <https://github.com/python-attrs/cattrs/issues/43>`_)

1.3.0 (2021-02-25)
------------------
* ``cattrs`` now has a benchmark suite to help make and keep cattrs the fastest it can be. The instructions on using it can be found under the `Benchmarking <https://cattrs.readthedocs.io/en/latest/benchmarking.html>` section in the docs.
  (`#123 <https://github.com/python-attrs/cattrs/pull/123>`_)
* Fix an issue unstructuring tuples of non-primitives.
  (`#125 <https://github.com/python-attrs/cattrs/issues/125>`_)
* ``cattrs`` now calls ``attr.resolve_types`` on ``attrs`` classes when registering un/structuring hooks.
* ``GenConverter`` structuring and unstructuring of ``attrs`` classes is significantly faster.

1.2.0 (2021-01-31)
------------------
* ``converter.unstructure`` now supports an optional parameter, `unstructure_as`, which can be used to unstructure something as a different type. Useful for unions.
* Improve support for union un/structuring hooks. Flesh out docs for advanced union handling.
  (`#115 <https://github.com/python-attrs/cattrs/pull/115>`_)
* Fix `GenConverter` behavior with inheritance hierarchies of `attrs` classes.
  (`#117 <https://github.com/python-attrs/cattrs/pull/117>`_) (`#116 <https://github.com/python-attrs/cattrs/issues/116>`_)
* Refactor `GenConverter.un/structure_attrs_fromdict` into `GenConverter.gen_un/structure_attrs_fromdict` to allow calling back to `Converter.un/structure_attrs_fromdict` without sideeffects.
  (`#118 <https://github.com/python-attrs/cattrs/issues/118>`_)

1.1.2 (2020-11-29)
------------------
* The default disambiguator will not consider non-required fields any more.
  (`#108 <https://github.com/python-attrs/cattrs/pull/108>`_)
* Fix a couple type annotations.
  (`#107 <https://github.com/python-attrs/cattrs/pull/107>`_) (`#105 <https://github.com/python-attrs/cattrs/issues/105>`_)
* Fix a `GenConverter` unstructuring issue and tests.

1.1.1 (2020-10-30)
------------------
* Add metadata for supported Python versions.
  (`#103 <https://github.com/python-attrs/cattrs/pull/103>`_)

1.1.0 (2020-10-29)
------------------
* Python 2, 3.5 and 3.6 support removal. If you need it, use a version below 1.1.0.
* Python 3.9 support, including support for built-in generic types (``list[int]`` vs ``typing.List[int]``).
* ``cattrs`` now includes functions to generate specialized structuring and unstructuring hooks. Specialized hooks are faster and support overrides (``omit_if_default`` and ``rename``). See the ``cattr.gen`` module.
* ``cattrs`` now includes a converter variant, ``cattr.GenConverter``, that automatically generates specialized hooks for attrs classes. This converter will become the default in the future.
* Generating specialized structuring hooks now invokes `attr.resolve_types <https://www.attrs.org/en/stable/api.html#attr.resolve_types>`_ on a class if the class makes use of the new PEP 563 annotations.
* ``cattrs`` now depends on ``attrs`` >= 20.1.0, because of ``attr.resolve_types``.
* Specialized hooks now support generic classes. The default converter will generate and use a specialized hook upon encountering a generic class.

1.0.0 (2019-12-27)
------------------
* ``attrs`` classes with private attributes can now be structured by default.
* Structuring from dictionaries is now more lenient: extra keys are ignored.
* ``cattrs`` has improved type annotations for use with Mypy.
* Unstructuring sets and frozensets now works properly.

0.9.1 (2019-10-26)
------------------
* Python 3.8 support.

0.9.0 (2018-07-22)
------------------
* Python 3.7 support.

0.8.1 (2018-06-19)
------------------
* The disambiguation function generator now supports unions of ``attrs`` classes and NoneType.

0.8.0 (2018-04-14)
------------------
* Distribution fix.

0.7.0 (2018-04-12)
------------------
* Removed the undocumented ``Converter.unstruct_strat`` property setter.
* | Removed the ability to set the ``Converter.structure_attrs`` instance field.
  | As an alternative, create a new ``Converter``::
  |
  | .. code-block:: python
  |
  |  >>> converter = cattr.Converter(unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE)
* Some micro-optimizations were applied; a ``structure(unstructure(obj))`` roundtrip
  is now up to 2 times faster.

0.6.0 (2017-12-25)
------------------
* Packaging fixes.
  (`#17 <https://github.com/python-attrs/cattrs/pull/17>`_)

0.5.0 (2017-12-11)
------------------
* structure/unstructure now supports using functions as well as classes for deciding the appropriate function.
* added `Converter.register_structure_hook_func`, to register a function instead of a class for determining handler func.
* added `Converter.register_unstructure_hook_func`, to register a function instead of a class for determining handler func.
* vendored typing is no longer needed, nor provided.
* Attributes with default values can now be structured if they are missing in the input.
  (`#15 <https://github.com/python-attrs/cattrs/pull/15>`_)
* | `Optional` attributes can no longer be structured if they are missing in the input.
  | In other words, this no longer works:
  |
  | .. code-block:: python
  |
  |    @attr.s
  |    class A:
  |        a: Optional[int] = attr.ib()
  |
  |    >>> cattr.structure({}, A)
  |
* ``cattr.typed`` removed since the functionality is now present in ``attrs`` itself.
  Replace instances of ``cattr.typed(type)`` with ``attr.ib(type=type)``.

0.4.0 (2017-07-17)
------------------
* `Converter.loads` is now `Converter.structure`, and `Converter.dumps` is now `Converter.unstructure`.
* Python 2.7 is supported.
* Moved ``cattr.typing`` to ``cattr.vendor.typing`` to support different vendored versions of typing.py for Python 2 and Python 3.
* Type metadata can be added to ``attrs`` classes using ``cattr.typed``.


0.3.0 (2017-03-18)
------------------
* Python 3.4 is no longer supported.
* Introduced ``cattr.typing`` for use with Python versions 3.5.2 and 3.6.0.
* Minor changes to work with newer versions of ``typing``.

  * Bare Optionals are not supported any more (use ``Optional[Any]``).

* Attempting to load unrecognized classes will result in a ValueError, and a helpful message to register a loads hook.
* Loading ``attrs`` classes is now documented.
* The global converter is now documented.
* ``cattr.loads_attrs_fromtuple`` and ``cattr.loads_attrs_fromdict`` are now exposed.


0.2.0 (2016-10-02)
------------------
* Tests and documentation.

0.1.0 (2016-08-13)
------------------
* First release on PyPI.
