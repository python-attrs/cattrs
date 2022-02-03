from cattrs._compat import is_bare, is_py37, is_py38

if is_py37 or is_py38:
    from typing import Dict, List

    def change_type_param(cl, new_params):
        if is_bare(cl):
            return cl[new_params]
        return cl.copy_with(new_params)

    List_origin = List
    Dict_origin = Dict


else:

    def change_type_param(cl, new_params):
        cl.__args__ = (new_params,)
        return cl

    List_origin = list
    Dict_origin = dict
