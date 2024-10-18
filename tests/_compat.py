import sys

is_py310 = sys.version_info[:2] == (3, 10)
is_py310_plus = sys.version_info >= (3, 10)
is_py311_plus = sys.version_info >= (3, 11)
is_py312_plus = sys.version_info >= (3, 12)


List_origin = list
Dict_origin = dict
