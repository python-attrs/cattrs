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

Classes
-------

