=======
History
=======

0.7.0 (2018-04-12)
------------------

* Removed the undocumented ``Converter.unstruct_strat`` property setter.
* Removed the ability to set the ``Converter.structure_attrs`` instance field.
  As an alternative, create a new ``Converter``::

.. code-block:: python

    >>> converter = cattr.Converter(unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE)
* Some micro-optimizations were applied; a ``structure(unstructure(obj))`` roundtrip
  is now up to 2 times faster.

0.6.0 (2017-12-25)
------------------
* Packaging fixes.
  (`#17 <https://github.com/Tinche/cattrs/pull/17>`_)

0.5.0 (2017-12-11)
------------------

* structure/unstructure now supports using functions as well as classes for deciding the appropriate function.
* added `Converter.register_structure_hook_func`, to register a function instead of a class for determining handler func.
* added `Converter.register_unstructure_hook_func`, to register a function instead of a class for determining handler func.
* vendored typing is no longer needed, nor provided.
* Attributes with default values can now be structured if they are missing in the input.
  (`#15 <https://github.com/Tinche/cattrs/pull/15>`_)
* `Optional` attributes can no longer be structured if they are missing in the input.
In other words, this no longer works:

.. code-block:: python

    @attr.s
    class A:
        a: Optional[int] = attr.ib()

    >>> cattr.structure({}, A)

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
