================================
What you can unstructure and how
================================

Unstructuring is intended to convert high-level, structured Python data (like
instances of complex classes) into simple, unstructured data (like
dictionaries).

Unstructuring is simpler than loading in that no target types are required.
Simply provide an argument to ``unstructure`` and ``cattrs`` will produce a
result based on the registered unstructuring hooks. A number of default
unstructuring hooks are documented here.

.. warning::

    When using Python 3.5 earlier or equal to 3.5.3 or Python 3.6.0, please use
    the bundled ``cattr.typing`` module instead of Python's standard ``typing``
    module. These versions of ``typing`` are incompatible with ``cattrs``. If
    your Python version is a later one, please use Python's ``typing`` instead.

Unstructuring is primarily done using :py:attr:`.Converter.unstructure`.

Primitive types and collections
-------------------------------

Primitive types (integers, floats, strings...) are simply passed through.
Collections are copied. There's relatively little value in unstructuring
these types directly as they are already unstructured and third-party
libraries tend to support them directly.

A useful use case for unstructuring collections is to create a deep copy of
a complex or recursive collection.

.. doctest::

    >>> # A dictionary of strings to lists of tuples of floats.
    >>> data = {'a': [(1.0, 2.0), (3.0, 4.0)]}
    >>>
    >>> copy = cattr.unstructure(data)
    >>> data == copy
    True
    >>> data is copy
    False


``attrs`` classes
-----------------

``attrs`` classes are supported out of the box. :class:`.Converter` s
support two unstructuring strategies:

    * ``UnstructureStrategy.AS_DICT`` - similar to ``attr.asdict``, unstructures ``attrs`` instances into dictionaries. This is the default.
    * ``UnstructureStrategy.AS_TUPLE`` - similar to ``attr.astuple``, unstructures ``attrs`` instances into tuples.

.. doctest::

    >>> @attr.s
    ... class C:
    ...     a = attr.ib()
    ...     b = attr.ib()
    ...
    >>> inst = C(1, 'a')
    >>>
    >>> converter = cattr.Converter(unstruct_strat=cattr.UnstructureStrategy.AS_TUPLE)
    >>>
    >>> converter.unstructure(inst)
    (1, 'a')

Mixing and matching strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Converters publicly expose two helper metods, :meth:`.Converter.unstructure_attrs_asdict`
and :meth:`.Converter.unstructure_attrs_astuple`. These methods can be used with
custom unstructuring hooks to selectively apply one strategy to instances of
particular classes.

Assume two nested ``attrs`` classes, ``A`` and ``B``; instances of ``A``
contain instances of ``B``. Instances of ``A`` should be unstructured as
dictionaries, and instances of ``B`` as tuples. Here's how to do this.

.. doctest::

    >>> @attr.s
    ... class A:
    ...     a = attr.ib()
    ...
    >>> @attr.s
    ... class B:
    ...     b = attr.ib()
    ...
    >>> inst = A(a=B(b=1))
    >>>
    >>> converter = cattr.Converter()
    >>> converter.register_unstructure_hook(B, converter.unstructure_attrs_astuple)
    >>>
    >>> converter.unstructure(inst)
    {'a': (1,)}

Of course, these methods can be used directly as well, without changing the converter strategy.

.. doctest::

    >>> @attr.s
    ... class C:
    ...     a = attr.ib()
    ...     b = attr.ib()
    ...
    >>> inst = C(1, 'a')
    >>>
    >>> converter = cattr.Converter()
    >>>
    >>> converter.unstructure_attrs_astuple(inst)  # Default is AS_DICT.
    (1, 'a')