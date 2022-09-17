==========
Converters
==========

All ``cattrs`` functionality is exposed through a :py:class:`cattrs.Converter` object.
Global ``cattrs`` functions, such as ``cattrs.unstructure()``, use a single
global converter. Changes done to this global converter, such as registering new
``structure`` and ``unstructure`` hooks, affect all code using the global
functions.

Global converter
----------------

A global converter is provided for convenience as ``cattrs.global_converter``.
The following functions implicitly use this global converter:

* ``cattrs.structure``
* ``cattrs.unstructure``
* ``cattrs.structure_attrs_fromtuple``
* ``cattrs.structure_attrs_fromdict``

Changes made to the global converter will affect the behavior of these
functions.

Larger applications are strongly encouraged to create and customize a different,
private instance of ``Converter``.

Converter objects
-----------------

To create a private converter, simply instantiate a ``cattrs.Converter``.
Currently, a converter contains the following state:

* a registry of unstructure hooks, backed by a ``singledispatch`` and a ``function_dispatch``.
* a registry of structure hooks, backed by a different ``singledispatch`` and ``function_dispatch``.
* a LRU cache of union disambiguation functions.
* a reference to an unstructuring strategy (either AS_DICT or AS_TUPLE).
* a ``dict_factory`` callable, used for creating ``dicts`` when dumping
  ``attrs`` classes using ``AS_DICT``.

Converters may be cloned using the :py:attr:`cattrs.Converter.copy` method.
The new copy may be changed through the `copy` arguments, but will retain all manually registered hooks from the original.

``cattrs.Converter``
--------------------

The ``Converter`` is a converter variant that automatically generates,
compiles and caches specialized structuring and unstructuring hooks for ``attrs``
classes.

``Converter`` differs from the ``cattrs.BaseConverter`` in the following ways:

* structuring and unstructuring of ``attrs`` classes is slower the first time, but faster every subsequent time
* structuring and unstructuring can be customized
* support for ``attrs`` classes with PEP563 (postponed) annotations
* support for generic ``attrs`` classes
* support for easy overriding collection unstructuring

``cattrs.BaseConverter``
------------------------

The ``BaseConverter`` is a simpler and slower Converter variant. It does no
code generation, so it may be faster on first-use which can be useful
in specific cases, like CLI applications where startup time is more
important than throughput.