import attr
import cattr


@attr.s(auto_attribs=True)
class Test:
    renamed: str = cattr.ib(src_key='class')


def test_structure_keywords():
    data = {'class': 'value'}
    obj = cattr.structure(data, Test)
    assert cattr.unstructure(obj) == data
