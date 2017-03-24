import sys

version_info = sys.version_info[0:3]
use_vendored_typing = (
    (3, 0, 0) <= version_info < (3, 5, 4) or
    (3, 6, 0) <= version_info < (3, 6, 1))

if use_vendored_typing:
    from .vendor.python3.typing import *  # noqa
    from .vendor.python3.typing import _Union  # noqa
else:
    from typing import *  # noqa
    from typing import GenericMeta
    from typing import _Union  # noqa

is_py2 = version_info[0] == 2
is_py3 = version_info[0] == 3

if is_py2:
    from functools32 import lru_cache
    from singledispatch import singledispatch
    unicode = unicode
    bytes = str
elif is_py3:
    from functools import lru_cache, singledispatch
    unicode = str
    bytes = bytes

