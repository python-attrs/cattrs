==================================
Generating unstructuring functions
==================================

``cattrs`` includes a module, ``cattr.gen``, which allows for generating and
compiling specialized functions for unstructuring ``attrs`` classes.

One reason for generating these functions in advance is that they can bypass
a lot of ``cattrs`` machinery and be significantly faster than normal ``cattrs``.

Another reason is that it's possible to override behavior on a per-attribute basis.

Currently, the overrides only support generating dict unstructuring functions
(as opposed to tuples), and only support ``omit_if_default``.

``omit_if_default``
-------------------

This override can be applied on a per-class or per-attribute basis. The generated
unstructuring function will skip unstructuring values that are equal to their
default or factory values.

.. doctest::

    >>> from cattr.gen import make_dict_unstructure_fn, override
    >>>
    >>> @attr.s
    ... class WithDefault:
    ...    a = attr.ib()
    ...    b = attr.ib(factory=dict)
    >>>
    >>> c = cattr.Converter()
    >>> c.register_unstructure_hook(WithDefault, make_dict_unstructure_fn(WithDefault, c, b=override(omit_if_default=True)))
    >>> c.unstructure(WithDefault(1))
    {'a': 1}

Note that the per-attribute value overrides the per-class value. A side-effect
of this rule is the ability to force the presence of a subset of fields.
For example, consider a class with a `DateTime` field and a factory for it:
skipping the unstructuring of the `DateTime` field would be inconsistent and
based on the current time. So we apply the `omit_if_default` rule to the class,
but not to the `DateTime` field.

.. doctest::

    >>> from pendulum import DateTime
    >>> from cattr.gen import make_dict_unstructure_fn, override
    >>>
    >>> @attr.s
    ... class TestClass:
    ...     a: Optional[int] = attr.ib(default=None)
    ...     b: DateTime = attr.ib(factory=DateTime.utcnow)
    >>>
    >>> c = cattr.Converter()
    >>> hook = make_dict_unstructure_fn(TestClass, c, omit_if_default=True, b=override(omit_if_default=False))
    >>> c.register_unstructure_hook(TestClass, hook)
    >>> c.unstructure(TestClass())
    {'b': ...}