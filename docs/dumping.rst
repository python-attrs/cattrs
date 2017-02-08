=========================
What you can dump and how
=========================

Dumping is intended to convert high-level, structured Python data (like
instances of complex classes) into simple, unstructured data (like
dictionaries).

Dumping is simpler than loading in that no target types are required. Simply
provide an argument to ``dumps`` and ``cattrs`` will produce a result based
on the registered dumping hooks. A number of default dumping hooks are
documented here.

Classes
-------

