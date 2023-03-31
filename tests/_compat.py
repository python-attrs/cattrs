from cattrs._compat import is_py37, is_py38

if is_py37 or is_py38:
    from typing import Dict, List

    List_origin = List
    Dict_origin = Dict


else:
    List_origin = list
    Dict_origin = dict
