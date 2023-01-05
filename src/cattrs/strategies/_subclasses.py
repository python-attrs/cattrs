"""Strategies for customizing subclass behaviors."""
from gc import collect
from typing import Dict, Optional, Tuple, Type, Union, List, Callable, Any

from ..converters import Converter, BaseConverter
from ..gen import AttributeOverride, make_dict_structure_fn, make_dict_unstructure_fn


def _make_subclasses_tree(cl: Type) -> List[Type]:
    return [cl] + [
        sscl for scl in cl.__subclasses__() for sscl in _make_subclasses_tree(scl)
    ]


def _has_subclasses(cl: Type, given_subclasses: Tuple[Type]):
    actual = set(cl.__subclasses__())
    given = set(given_subclasses)
    return bool(actual & given)


def _get_union_type(cl: Type, given_subclasses_tree: Tuple[Type]) -> Type:
    actual_subclass_tree = tuple(_make_subclasses_tree(cl))
    class_tree = tuple(set(actual_subclass_tree) & set(given_subclasses_tree))
    union_type = Union[class_tree]
    return union_type


def include_subclasses(
    cl: Type,
    converter: Converter,
    subclasses: Optional[Tuple[Type]] = None,
    union_strategy: Optional[Callable[[Any, BaseConverter], Any]] = None,
    overrides: Optional[Dict[str, AttributeOverride]] = None,
) -> None:
    """
    Modify the given converter so that the attrs/dataclass `cl` is un/structured as if
    it was a union of itself and all its subclasses that are defined at the time when
    this strategy is applied.

    Subclasses are detected using the `__subclasses__` method, or they can be explicitly
    provided.

    overrides is a mapping of some or all the parent class field names to attribute
    overrides instantiated with :func:`cattrs.gen.override`
    """
    # Due to https://github.com/python-attrs/attrs/issues/1047
    collect()
    if subclasses is not None:
        parent_subclass_tree = (cl,) + subclasses
    else:
        parent_subclass_tree = tuple(_make_subclasses_tree(cl))

    if overrides is None:
        overrides = {}

    # The iteration approach is required if subclasses are more than one level deep: ? n;
    for cl in parent_subclass_tree:
        if not _has_subclasses(cl, parent_subclass_tree):
            continue

        # We re-create a reduced union type to handle the following case:
        # >>> converter.structure(d, as=Child)
        # and the `as=Child` will be transformed to a union type of itself and its
        # subtypes, that way we guarantee that the returned object will not be the
        # parent.
        subclass_union = _get_union_type(cl, parent_subclass_tree)

        if union_strategy is None:
            unstruct_hook = gen_unstructure_hook(converter, cl, overrides)
            struct_hook = gen_structure_hook(converter, cl, subclass_union, overrides)
        else:
            union_strategy(subclass_union, converter)
            unstruct_hook = converter._unstructure_func.dispatch(subclass_union)
            struct_hook = converter._union_struct_registry[subclass_union]

        # Note: the closure approach is needed due to python scoping rule. If we define
        # the lambda here, the last class in the iteration will be used in all lambdas.
        cls_is_cl = gen_cls_is_cl(cl)

        # This needs to use function dispatch, using singledispatch will again
        # match A and all subclasses, which is not what we want.
        converter.register_unstructure_hook_func(cls_is_cl, unstruct_hook)
        converter.register_structure_hook_func(cls_is_cl, struct_hook)


def gen_unstructure_hook(
    converter: Converter,
    cl: Type,
    overrides: Optional[Dict[str, AttributeOverride]] = None,
):
    # This hook is for instances of the class cl, but not instances of subclasses.
    base_hook = make_dict_unstructure_fn(cl, converter, **overrides)

    def unstructure_hook(val: cl, c=converter) -> Dict:
        """
        If val is an instance of the class `cl`, use the hook.

        If val is an instance of a subclass, dispatch on its exact runtime type.
        """
        if val.__class__ is cl:
            return base_hook(val)
        return c.unstructure(val, unstructure_as=val.__class__)

    return unstructure_hook


def gen_structure_hook(
    converter: Converter,
    cl: Type,
    subclass_union: Type,
    overrides: Optional[Dict[str, AttributeOverride]] = None,
) -> Callable:
    dis_fn = converter._get_dis_func(subclass_union)
    base_struct_hook = make_dict_structure_fn(cl, converter, **overrides)

    def structure_hook(val: dict, _, c=converter, cl=cl) -> cl:
        """
        If val is an instance of the class `cl`, use the hook.

        If val is an instance of a subclass, dispatch on its exact runtime type.
        """
        dis_cl = dis_fn(val)
        if dis_cl is cl:
            return base_struct_hook(val, cl)
        return c.structure(val, dis_cl)

    return structure_hook


def gen_cls_is_cl(cl):
    return lambda cls: cls is cl
