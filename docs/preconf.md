# Preconfigured Converters

The {mod}`cattrs.preconf` package contains factories for preconfigured converters, specifically adjusted for particular serialization libraries.

For example, to get a converter configured for _orjson_:

```{doctest}

>>> from cattrs.preconf.orjson import make_converter

>>> converter = make_converter() # Takes the same parameters as the `cattrs.Converter`
```

Converters obtained this way can be customized further, just like any other converter.

For compatibility and performance reasons, these converters are usually configured to unstructure differently than ordinary `Converters`.
A couple of examples:
* the {class}`_orjson_ converter <cattrs.preconf.orjson.OrjsonConverter>` is configured to pass `datetime` instances unstructured since _orjson_ can handle them faster.
* the {class}`_msgspec_ JSON converter <cattrs.preconf.msgspec.MsgspecJsonConverter>` is configured to pass through some dataclasses and _attrs_classes,
if the output is identical to what normal unstructuring would have produced, since _msgspec_ can handle them faster.

The intended usage is to pass the unstructured output directly to the underlying library,
or use `converter.dumps` which will do it for you.

These converters support all [default hooks](defaulthooks.md)
and the following additional classes and type annotations,
both for structuring and unstructuring:

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

Third-party libraries can be specified as optional (extra) dependencies on _cattrs_ during installation.
Optional install targets should match the name of the {mod}`cattrs.preconf` modules.

```console
# Using pip
$ pip install cattrs[ujson]

# Using pdm
$ pdm add cattrs[orjson]

# Using poetry
$ poetry add --extras tomlkit cattrs
```


## Standard Library _json_

Found at {mod}`cattrs.preconf.json`.

Bytes are serialized as base 85 strings. Counters are serialized as dictionaries. Sets are serialized as lists, and deserialized back into sets. `datetime` s and `date` s are serialized as ISO 8601 strings.


## _orjson_

Found at {mod}`cattrs.preconf.orjson`.

Bytes are un/structured as base 85 strings.
Sets are unstructured into lists, and structured back into sets.
`datetime` s and `date` s are passed through to be unstructured into RFC 3339 by _orjson_ itself.
Typed named tuples are unstructured into ordinary tuples, and then into JSON arrays by _orjson_.

_orjson_ doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807.
_orjson_ only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization.


## _msgspec_

Found at {mod}`cattrs.preconf.msgspec`.
Only JSON functionality is currently available, other formats supported by msgspec to follow in the future.

[_msgspec_ structs](https://jcristharif.com/msgspec/structs.html) are supported, but not composable - a struct will be handed over to _msgspec_ directly, and _msgspec_ will handle and all of its fields, recursively.
_cattrs_ may get more sophisticated handling of structs in the future.

[_msgspec_ strict mode](https://jcristharif.com/msgspec/usage.html#strict-vs-lax-mode) is used by default.
This can be customized by changing the {meth}`encoder <cattrs.preconf.msgspec.MsgspecJsonConverter.encoder>` attribute on the converter.

What _cattrs_ calls _unstructuring_ and _structuring_, _msgspec_ calls [`to_builtins` and `convert`](https://jcristharif.com/msgspec/converters.html).
What _cattrs_ refers to as _dumping_ and _loading_, _msgspec_ refers to as [`encoding` and `decoding`](https://jcristharif.com/msgspec/usage.html).

Compatibility notes:
- Bytes are un/structured as base 64 strings directly by _msgspec_ itself.
- _msgspec_ [encodes special float values](https://jcristharif.com/msgspec/supported-types.html#float) (`NaN, Inf, -Inf`) as `null`.
- `datetime` s and `date` s are passed through to be unstructured into RFC 3339 by _msgspec_ itself.
- _attrs_ classes, dataclasses and sequences are handled directly by _msgspec_ if possible, otherwise by the normal _cattrs_ machinery.
This means it's possible the validation errors produced may be _msgspec_ validation errors instead of _cattrs_ validation errors.

This converter supports {meth}`get_loads_hook() <cattrs.preconf.msgspec.MsgspecJsonConverter.get_loads_hook>` and {meth}`get_dumps_hook() <cattrs.preconf.msgspec.MsgspecJsonConverter.get_loads_hook>`.
These are factories for dumping and loading functions (as opposed to unstructuring and structuring); the hooks returned by this may be further optimized to offload as much work as possible to _msgspec_.

```python
>>> from cattrs.preconf.msgspec import make_converter

>>> @define
... class Test:
...     a: int

>>> converter = make_converter()
>>> dumps = converter.get_dumps_hook(A)

>>> dumps(Test(1))  # Will use msgspec directly.
b'{"a":1}'
```

Due to its complexity, this converter is currently _provisional_ and may slightly change as the best integration patterns are discovered.

_msgspec_ doesn't support PyPy.

```{versionadded} 24.1.0

```

## _ujson_

Found at {mod}`cattrs.preconf.ujson`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets. `datetime` s and `date` s are serialized as ISO 8601 strings.

_ujson_ doesn't support integers less than -9223372036854775808, and greater than 9223372036854775807, nor does it support `float('inf')`.


## _msgpack_

Found at {mod}`cattrs.preconf.msgpack`.

Sets are serialized as lists, and deserialized back into sets. `datetime` s are serialized as UNIX timestamp float values. `date` s are serialized as midnight-aligned UNIX timestamp float values.

_msgpack_ doesn't support integers less than -9223372036854775808, and greater than 18446744073709551615.

When parsing msgpack data from bytes, the library needs to be passed `strict_map_key=False` to get the full range of compatibility.


## _cbor2_

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

```{versionadded} 23.1.0

```

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

Frozensets are serialized as lists, and deserialized back into frozensets.
`date` s are serialized as ISO 8601 strings.
Typed named tuples are unstructured into ordinary tuples, and then into YAML arrays by _pyyaml_.

## _tomlkit_

Found at {mod}`cattrs.preconf.tomlkit`.

Bytes are serialized as base 85 strings. Sets are serialized as lists, and deserialized back into sets.
Tuples are serialized as lists, and deserialized back into tuples.
_tomlkit_ only supports mappings with string keys so mappings will have their keys stringified before serialization, and destringified during deserialization. `date` s are serialized as ISO 8601 strings.
