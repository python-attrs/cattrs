"""Tests for the typed wrapper."""
from cattr import typed
from cattr.metadata import TYPE_METADATA_KEY
from cattr._compat import Any


def test_existing_metadata():
    """
    `typed` does not clobber metadata.
    """

    res = typed(Any, metadata={'test': 'test'})

    assert res.metadata[TYPE_METADATA_KEY] is Any
    assert res.metadata['test'] == 'test'
