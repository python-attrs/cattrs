import sys
version_info = sys.version_info[0:3]
is_py2 = version_info[0] == 2

if is_py2:
    from .python2.typing import *  # noqa
    from .python2.typing import _Union  # noqa
else:
    from .python3.typing import *  # noqa
    from .python3.typing import _Union  # noqa
