import sys

is_py38 = sys.version_info[:2] == (3, 8)
is_py39 = sys.version_info[:2] == (3, 9)
is_py39_plus = sys.version_info >= (3, 9)
is_py310 = sys.version_info[:2] == (3, 10)
is_py310_plus = sys.version_info >= (3, 10)
is_py311_plus = sys.version_info >= (3, 11)
is_py312_plus = sys.version_info >= (3, 12)

if is_py38:
    from typing import Dict, List

    List_origin = List
    Dict_origin = Dict


else:
    List_origin = list
    Dict_origin = dict
