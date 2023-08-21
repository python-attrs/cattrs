# Preconfigured Converters

The {mod}`cattrs.preconf` package contains factories for preconfigured converters, specifically adjusted for particular serialization libraries.

For example, to get a converter configured for BSON:

```{doctest}

>>> from cattrs.preconf.bson import make_converter

>>> converter = make_converter() # Takes the same parameters as the `cattrs.Converter`
```

Converters obtained this way can be customized further, just like any other converter.

These converters support the following classes and type annotations, both for structuring and unstructuring:

- `str`, `bytes`, `int`, `float`, `pathlib.Path` int enums, string enums
- _attrs_ classes and dataclasses
- lists, homogenous tuples, heterogenous tuples, dictionaries, counters, sets, frozensets
- optionals
- sequences, mutable sequences, mappings, mutable mappings, sets, mutable sets
- `datetime.datetime`, `datetime.date`

```{versionadded} 22.1.0
All preconf converters now have `loads` and `dumps` methods, which combine un/structuring and the de/serialization logic from their underlying libraries.
```

```{doctest}

>>> from cattrs.preconf.json import make_converter

>>> converter = make_converter()

>>> @define
... class Test:
...     a: int

>>> converter.dumps(Test(1))
'{"a": 1}'
```

Particular libraries may have additional constraints documented below.

Third-party libraries can be specified as optional (extra) dependencies on `cattrs` during installation.
Optional install targets should match the name of the {mod}`cattrs.preconf` modules.

```console
# Using pip
pip install cattrs[ujson]

# Using poetry
poetry add --extras tomlkit cattrs
```

## Standard Library _json_

Found at {mod}`cattrs.preconf.json`.

Bytes are serialized as base 85 strings. Counters are serialized as dictionaries. Sets are serialized as lists, and deserialized back into sets. `datetime` s and `date` s are serialized as ISO 8601 strings.

## _ujson_

Found at {mod}`cattrs.preconf.ujson`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. `datetime` s and `date` s are serialized as ISO 8601 strings.

`ujson` doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807, nor does it support `float('inf')`.

## _orjson_

Found at {mod}`cattrs.preconf.orjson`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. `datetime` s and `date` s are serialized as ISO 8601 strings.

_orjson_ doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807.
_orjson_ only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.

## _msgpack_

Found at {mod}`cattrs.preconf.msgpack`.

Sets are serialized as lists, and deserialized back into sets. `datetime` s are serialized as UNIX timestamp float values. `date` s are serialized as midnight-aligned UNIX timestamp float values.

_msgpack_ doesn't support integers less than -9223372036854775808, and greater than 18446744073709551615.

When parsing msgpack data from bytes, the library needs to be passed `strict_map_key=False` to get the full range of compatibility.

## _cbor2_

```{versionadded} 23.1.0

```

Found at {mod}`cattrs.preconf.cbor2`.

_cbor2_ implements a fully featured CBOR encoder with several extensions for handling shared references, big integers, rational numbers and so on.

Sets are serialized and deserialized to sets.
Tuples are serialized as lists.

`datetime` s are serialized as a text string by default (CBOR Tag 0).
Use keyword argument `datetime_as_timestamp=True` to encode as UNIX timestamp integer/float (CBOR Tag 1)
**note:** this replaces timezone information as UTC.

`date` s are serialized as ISO 8601 strings.

Use keyword argument `canonical=True` for efficient encoding to the smallest binary output.

Floats can be forced to smaller output by casting to lower-precision formats by casting to `numpy` floats (and back to Python floats).
Example: `float(np.float32(value))` or `float(np.float16(value))`

## _bson_

Found at {mod}`cattrs.preconf.bson`. Tested against the _bson_ module bundled with the _pymongo_ library, not the standalone PyPI _bson_ package.

Sets are serialized as lists, and deserialized back into sets.

_bson_ doesn't support integers less than -9223372036854775808 or greater than 9223372036854775807 (64-bit signed).
_bson_ does not support null bytes in mapping keys.
_bson_ only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.
The _bson_ datetime representation doesn't support microsecond accuracy.
`date` s are serialized as ISO 8601 strings.

When encoding and decoding, the library needs to be passed `codec_options=bson.CodecOptions(tz_aware=True)` to get the full range of compatibility.

## _pyyaml_

Found at {mod}`cattrs.preconf.pyyaml`.

Frozensets are serialized as lists, and deserialized back into frozensets. `date` s are serialized as ISO 8601 strings.

## _tomlkit_

Found at {mod}`cattrs.preconf.tomlkit`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets.
Tuples are serialized as lists, and deserialized back into tuples.
_tomlkit_ only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization. `date` s are serialized as ISO 8601 strings.
