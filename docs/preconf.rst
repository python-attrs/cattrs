========================
Preconfigured Converters
========================

The ``cattr.preconf`` package contains factories for preconfigured converters, specifically adjusted for particular serialization libraries.

For example, to get a converter configured for BSON:

.. doctest::

  >>> from cattr.preconf.bson import make_converter
  >>> converter = make_converter()   # Takes the same parameters as the ``GenConverter``

Converters obtained this way can be customized further, just like any other converter.

These converters support the following classes and type annotations, both for structuring and unstructuring:

* ``str``, ``bytes``, ``int``, ``float``, int enums, string enums
* ``attrs`` classes and ``dataclasses``
* lists, homogenous tuples, heterogenous tuples, dictionaries, counters, sets, frozensets
* optionals
* sequences, mutable sequences, mappings, mutable mappings, sets, mutable sets
* ``datetime.datetime``

Particular libraries may have additional constraints documented below.

Standard library ``json``
-------------------------

Found at ``cattr.preconf.json``.

Bytes are serialized as base 85 strings. Counters are serialized as dictionaries. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.


``ujson``
---------

Found at ``cattr.preconf.ujson``.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.

``ujson`` doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807, nor does it support `float('inf')`.


``orjson``
---------

Found at ``cattr.preconf.orjson``.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.

``orjson`` doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807.
``orjson`` only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.


``msgpack``
-----------

Found at ``cattr.preconf.msgpack``.

Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as UNIX timestamp float values.

``msgpack`` doesn't support integers less than -9223372036854775808, and greater than 18446744073709551615.

When parsing msgpack data from bytes, the library needs to be passed ``strict_map_key=False`` to get the full range of compatibility.


``bson``
--------

Found at ``cattr.preconf.bson``.

Sets are serialized as lists, and deserialized back into sets.

``bson`` doesn't support integers less than -9223372036854775808, and greater than 18446744073709551615.
``bson`` does not support null bytes in mapping keys.
The ``bson`` datetime representation doesn't support microsecond accuracy.



``pyyaml``
----------

Found at ``cattr.preconf.pyyaml``.

Frozensets are serialized as lists, and deserialized back into frozensets.


``tomlkit``
----------

Found at ``cattr.preconf.tomlkit``.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets.
Tuples are serialized as lists, and deserialized back into tuples.
``tomlkit`` only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.
