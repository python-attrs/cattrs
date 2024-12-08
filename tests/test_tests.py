from .untyped import gen_attr_names


def test_gen_attr_names():
    """We can generate a lot of attribute names."""
    assert len(list(gen_attr_names())) == 697

    # No duplicates!
    assert len(list(gen_attr_names())) == len(set(gen_attr_names()))
