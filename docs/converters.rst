==========
Converters
==========

All ``cattrs`` functionality is exposed through a ``cattr.Converter`` object.
Global ``cattrs`` functions, such as ``cattr.unstructure()``, use a single
global converter. Changes done to this global converter, such as registering new
``structure`` and ``unstructure`` hooks, affect all code using the global
functions.

Global converter
----------------

A global converter is provided for convenience as ``cattr.global_converter``.
The following functions implicitly use this global converter:

* ``cattr.structure``
* ``cattr.unstructure``
* ``cattr.structure_attr_fromtuple``
* ``cattr.structure_attr_fromdict``

Changes made to the global converter will affect the behavior of these
functions.

Larger applications are strongly encouraged to create and customize a different,
private instance of ``Converter``.

Converter objects
-----------------

To create a private converter, simply instantiate a ``cattr.Converter``.
Currently, a converter contains the following state:

* a registry of unstructure hooks, backed by a ``singledispatch`` and a ``function_dispatch``.
* a registry of structure hooks, backed by a different ``singledispatch`` and ``function_dispatch``.
* a LRU cache of union disambiguation functions.
* a reference to an unstructuring strategy (either AS_DICT or AS_TUPLE).
* a ``dict_factory`` callable, used for creating ``dicts`` when dumping
  ``attrs`` classes using ``AS_DICT``.

``cattr.GenConverter``
----------------------

The ``GenConverter`` is a converter subclass that automatically generates,
compiles and caches specialized structuring and unstructuring hooks for ``attrs``
classes.

``GenConverter`` differs from the old ``cattr.Converter`` in the following ways:

* structuring and unstructuring of ``attrs`` classes is slower the first time, but faster every subsequent time
* structuring and unstructuring can be customized
* support for ``attrs`` classes with PEP563 (postponed) annotations
* support for generic ``attrs`` classes



The ``GenConverter`` will become the default converter type in a later release.