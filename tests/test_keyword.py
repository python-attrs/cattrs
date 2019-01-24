import attr
import cattr


@attr.s
class MyClass(object):
    renamed = cattr.ib(src_key='class', type=str)


def test_structure_keywords():

    data = {'class': 'value'}
    obj = cattr.structure(data, MyClass)
    assert cattr.unstructure(obj) == data
