==========
Strategies
==========

*cattrs* ships with a number of *strategies* for customizing un/structuring behavior.

Strategies are prepackaged, high-level patterns for quickly and easily applying complex customizations to a converter.

Tagged Unions
*************

*Found at :py:func:`cattrs.strategies.configure_tagged_union`.*

The *tagged union* strategy allows for un/structuring a union of classes by including an additional field (the *tag*) in the unstructured representation.
Each tag value is associated with a member of the union.

.. doctest::

    >>> from cattrs.strategies.unions import configure_tagged_union
    >>> from cattrs import Converter
    >>> converter = Converter()
    >>> @define
    ... class A:
    ...     a: int
    >>>
    >>> @define
    ... class B:
    ...     b: str
    >>>
    >>> configure_tagged_union(A | B, converter)
    >>> converter.unstructure(A(1), unstructure_as=A | B)
    {'a': 1, '_type': 'A'}

By default, the tag field name is `_type` and the tag value is the `__name__` of the union member.
Both the field name and value can be overriden.