"""Strategies for customizing subclass behaviors."""
from gc import collect
from typing import Dict, Optional, Tuple, Type, Union, List, Callable

from ..converters import Converter


def _make_subclasses_tree(cl: Type) -> List[Type]:
    return [cl] + [
        sscl for scl in cl.__subclasses__() for sscl in _make_subclasses_tree(scl)
    ]


def _has_subclasses(cl):
    return bool(cl.__subclasses__())


def include_subclasses(
    cl: Type, converter: Converter, subclasses: Optional[Tuple[Type]] = None
) -> None:
    """
    Modify the given converter so that the attrs/dataclass `cl` is
    un/structured as if it was a union of itself and all its subclasses
    that are defined at the time when this strategy is applied.

    Subclasses are detected using the `__subclasses__` method, or
    they can be explicitly provided.
    """
    # Due to https://github.com/python-attrs/attrs/issues/1047
    collect()

    can_handle, unstructure_a = gen_unstructure_handling_pair(converter, cl)

    # This needs to use function dispatch, using singledispatch will again
    # match A and all subclasses, which is not what we want.
    converter.register_unstructure_hook_func(can_handle, unstructure_a)

    if subclasses is not None:
        parent_subclass_tree = (cl, subclasses)
    else:
        parent_subclass_tree = tuple(_make_subclasses_tree(cl))

    for cl in parent_subclass_tree:
        if not _has_subclasses(cl):
            continue

        can_handle, structure_a = gen_structure_handling_pair(converter, cl)
        converter.register_structure_hook_func(can_handle, structure_a)


def gen_unstructure_handling_pair(converter: Converter, cl: Type):
    # This hook is for instances of A, but not instances of subclasses.
    base_hook = converter.gen_unstructure_attrs_fromdict(cl)

    def unstructure_a(val: cl, c=converter) -> Dict:
        """
        If val is an instance of `A`, use the hook.

        If val is an instance of a subclass, dispatch on its exact
        runtime type.
        """
        if val.__class__ is cl:
            return base_hook(val)
        return c.unstructure(val, unstructure_as=val.__class__)

    return (lambda cls: cls is cl, unstructure_a)


def gen_structure_handling_pair(converter: Converter, cl: Type) -> Tuple[Callable]:
    class_tree = _make_subclasses_tree(cl)
    subclass_union = Union[tuple(class_tree)]
    dis_fn = converter._get_dis_func(subclass_union)
    base_struct_hook = converter.gen_structure_attrs_fromdict(cl)

    def structure_a(val: dict, _, c=converter, cl=cl) -> cl:
        dis_cl = dis_fn(val)
        if dis_cl is cl:
            return base_struct_hook(val, cl)
        return c.structure(val, dis_cl)

    return (lambda cls: cls is cl, structure_a)
