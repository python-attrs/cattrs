from cattr._compat import is_py37, is_py38, is_bare

if is_py37 or is_py38:

    def change_type_param(cl, new_params):
        if is_bare(cl):
            return cl[new_params]
        return cl.copy_with(new_params)


else:

    def change_type_param(cl, new_params):
        cl.__args__ = (new_params,)
        return cl
