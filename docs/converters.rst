==========
Converters
==========

All ``cattrs`` functionality is exposed through a ``cattr.Converter`` object.
Global ``cattrs`` functions, such as ``cattr.loads()``, use a single global
converter. Changes done to this global converter, such as registering new
``loads`` and ``dumps`` hooks, affect all code using the global functions.

Converter objects
-----------------

To create a private converter, simply instantiate a ``cattr.Converter``.
Currently, a converter contains the following state:

* a registry of dumps hooks, backed by a ``singledispatch``.
* a registry of loads hooks, backed by a different ``singledispatch``.
* a LRU cache of union disambiguation functions.
* a ``dict_factory`` callable, used for creating ``dicts`` when dumping
  ``attrs`` classes.