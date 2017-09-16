import sys

version_info = sys.version_info[0:3]
use_vendored_typing = (
    (3, 0, 0) <= version_info < (3, 5, 4) or
    (3, 6, 0) <= version_info < (3, 6, 1))
is_py2 = version_info[0] == 2
is_py3 = version_info[0] == 3

from typing import *  # noqa
from typing import _Union  # noqa

if is_py2:
    from functools32 import lru_cache
    from singledispatch import singledispatch
    unicode = unicode  # noqa
    bytes = str
else:
    from functools import lru_cache, singledispatch  # noqa
    unicode = str
    bytes = bytes
