"""Metadata utilities."""
from attr import attr, NOTHING


TYPE_METADATA_KEY = "cattr_type_metadata"


def typed(type, default=NOTHING, validator=None,
          repr=True, cmp=True, hash=True, init=True,
          convert=None, metadata={}):
    """Just like `attr.ib`, but with type metadata."""
    if not metadata:
        metadata = {TYPE_METADATA_KEY: type}
    else:
        metadata[TYPE_METADATA_KEY] = type
    return attr(default, validator, repr, cmp, hash, init, convert, metadata)
