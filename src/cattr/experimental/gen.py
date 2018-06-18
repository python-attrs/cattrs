"""Generate tailored structuring and unstructuring functions."""
from typing import Callable, Sequence, Type

from attr import Attribute, fields


def make_unstruct_fn(cl):
    """Given an attrs class, make an unstructuring function for it."""
    return make_unstruct_fn(cl)


def make_dict_unstruct_fn_from_attrs(cl, attrs=None):
    # type: (Type, Sequence[Attribute]) -> Callable
    """Make a dict unstructuring function for a given attribute list.

    Given an attrs class like:

    @attr.s
    class C:
        a: int = attr.ib()
        b: float = attr.ib()

    the a function similar to the following will be generated:

    def _unstruct_fromdict_C(d):
        return C(
            int(d['a']),
            float(d['b']),
        )
    """
    if attrs is None:
        attrs = fields(cl)

    fn_name = '_unstruct_fromdict_{}'.format(cl.__name__)

    lines = []
    lines.append('def {}(d):'.format(fn_name))
    lines.append('    return {}('.format(cl.__name__))

    for a in attrs:
        lines.append('        d["{}"],'.format(a.name))

    lines.append('    )')

    globs = {
        cl.__name__: cl,
    }
    locs = {}

    code = "\n".join(lines)
    eval(compile(code, 'cattr_unstruct.py', 'exec'), globs, locs)

    return locs[fn_name]
