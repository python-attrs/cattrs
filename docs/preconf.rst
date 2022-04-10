========================
Preconfigured converters
========================

The :py:mod:`cattrs.preconf` package contains factories for preconfigured converters, specifically adjusted for particular serialization libraries.

For example, to get a converter configured for BSON:

.. doctest::

  >>> from cattrs.preconf.bson import make_converter
  >>> converter = make_converter()   # Takes the same parameters as the ``Converter``

Converters obtained this way can be customized further, just like any other converter.

These converters support the following classes and type annotations, both for structuring and unstructuring:

* ``str``, ``bytes``, ``int``, ``float``, int enums, string enums
* ``attrs`` classes and ``dataclasses``
* lists, homogenous tuples, heterogenous tuples, dictionaries, counters, sets, frozensets
* optionals
* sequences, mutable sequences, mappings, mutable mappings, sets, mutable sets
* ``datetime.datetime``

.. versionadded:: 22.1.0
  All preconf converters now have ``loads`` and ``dumps`` methods, which combine un/structuring and the de/serialization logic from their underlying libraries.

.. doctest::

  >>> from cattrs.preconf.json import make_converter
  >>> converter = make_converter()

  >>> @define
  ... class Test:
  ...     a: int
  >>>

  >>> converter.dumps(Test(1))
  '{"a": 1}'

Particular libraries may have additional constraints documented below.

Standard library ``json``
-------------------------

Found at :py:mod:`cattrs.preconf.json`.

Bytes are serialized as base 85 strings. Counters are serialized as dictionaries. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.


``ujson``
---------

Found at :py:mod:`cattrs.preconf.ujson`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.

``ujson`` doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807, nor does it support `float('inf')`.


``orjson``
----------

Found at :py:mod:`cattrs.preconf.orjson`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as ISO 8601 strings.

``orjson`` doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807.
``orjson`` only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.


``msgpack``
-----------

Found at :py:mod:`cattrs.preconf.msgpack`.

Sets are serialized as lists, and deserialized back into sets. ``datetime`` s are serialized as UNIX timestamp float values.

``msgpack`` doesn't support integers less than -9223372036854775808, and greater than 18446744073709551615.

When parsing msgpack data from bytes, the library needs to be passed ``strict_map_key=False`` to get the full range of compatibility.


``bson``
--------

Found at :py:mod:`cattrs.preconf.bson`. Tested against the ``bson`` module bundled with the ``pymongo`` library, not the standalone PyPI ``bson`` package.

Sets are serialized as lists, and deserialized back into sets.

``bson`` doesn't support integers less than -9223372036854775808 or greater than 9223372036854775807 (64-bit signed).
``bson`` does not support null bytes in mapping keys.
``bson`` only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.
The ``bson`` datetime representation doesn't support microsecond accuracy.

When encoding and decoding, the library needs to be passed ``codec_options=bson.CodecOptions(tz_aware=True)`` to get the full range of compatibility.



``pyyaml``
----------

Found at :py:mod:`cattrs.preconf.pyyaml`.

Frozensets are serialized as lists, and deserialized back into frozensets.


``tomlkit``
-----------

Found at :py:mod:`cattrs.preconf.tomlkit`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets.
Tuples are serialized as lists, and deserialized back into tuples.
``tomlkit`` only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.
