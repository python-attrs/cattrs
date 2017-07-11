=======
History
=======

0.4.0 (UNRELEASED)
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
