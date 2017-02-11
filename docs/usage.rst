=====
Usage
=====

To use cattrs in a project::

    import cattr

Converters
----------

Every operation in ``cattrs`` is done using a ``Converter`` instance. A global
converter is provided for convenience as ``cattr.global_converter``. The
following functions implicitely use this global converter:

* ``cattr.loads``
* ``cattr.dumps``
* ``cattr.loads_attr_fromtuple``
* ``cattr.loads_attr_fromdict``

Changes made to the global converter will affect the behavior of these
functions.

Larger applications are strongly encouraged to create and customize a different,
private instance of ``Converter``.