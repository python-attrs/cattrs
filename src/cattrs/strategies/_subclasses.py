"""Strategies for customizing subclass behaviors."""
from gc import collect
from typing import Dict, Optional, Tuple, Type, Union, List, Callable, Any, get_args

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


def _get_union_type(cl: Type, given_subclasses_tree: Tuple[Type]) -> Optional[Type]:
    actual_subclass_tree = tuple(_make_subclasses_tree(cl))
    class_tree = tuple(set(actual_subclass_tree) & set(given_subclasses_tree))
    if len(class_tree) >= 2:
        union_type = Union[class_tree]
    else:
        union_type = None
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

    # The iteration approach is required if subclasses are more than one level deep:
    for i, cl in enumerate(parent_subclass_tree):
        # We re-create a reduced union type to handle the following case:
        #
        #     converter.structure(d, as=Child)
        #
        # In the above, the `as=Child` argument will be transformed to a union type of
        # itself and its subtypes, that way we guarantee that the returned object will
        # not be the parent.
        subclass_union = _get_union_type(cl, parent_subclass_tree)

        def cls_is_cl(cls, _cl=cl):
            return cls is _cl

        base_struct_hook = make_dict_structure_fn(cl, converter, **overrides)
        base_unstruct_hook = make_dict_unstructure_fn(cl, converter, **overrides)

        if union_strategy is None:
            if subclass_union is None:

                def struct_hook(
                    val: dict, _, _cl=cl, _base_hook=base_struct_hook
                ) -> cl:
                    return _base_hook(val, _cl)

            else:
                dis_fn = converter._get_dis_func(subclass_union)

                def struct_hook(
                    val: dict,
                    _,
                    _c=converter,
                    _cl=cl,
                    _base_hook=base_struct_hook,
                    _dis_fn=dis_fn,
                ) -> cl:
                    """
                    If val is disambiguated to the class `cl`, use its base hook.

                    If val is disambiguated to a subclass, dispatch on its exact runtime
                    type.
                    """
                    dis_cl = _dis_fn(val)
                    if dis_cl is _cl:
                        return _base_hook(val, _cl)
                    return _c.structure(val, dis_cl)

            def unstruct_hook(
                val: parent_subclass_tree[0],
                _c=converter,
                _cl=cl,
                _base_hook=base_unstruct_hook,
            ) -> Dict:
                """
                If val is an instance of the class `cl`, use the hook.

                If val is an instance of a subclass, dispatch on its exact runtime type.
                """
                if val.__class__ is _cl:
                    return _base_hook(val)
                return _c.unstructure(val, unstructure_as=val.__class__)

            unstruct_predicate = cls_is_cl
        else:
            if subclass_union is not None:
                union_strategy(subclass_union, converter)
                struct_hook = converter._union_struct_registry[subclass_union]
            else:
                struct_hook = None

            if i == 0 and subclass_union is not None:
                if subclass_union is not None:
                    union_classes = get_args(subclass_union)
                else:
                    union_classes = ()

                def cls_is_in_union(cls, _union_classes=union_classes):
                    return cls in _union_classes

                unstruct_hook = converter._unstructure_func.dispatch(subclass_union)
                unstruct_predicate = cls_is_in_union
            else:
                unstruct_hook = None
                unstruct_predicate = None

        # This needs to use function dispatch, using singledispatch will again
        # match A and all subclasses, which is not what we want.
        if unstruct_hook is not None:
            converter.register_unstructure_hook_func(unstruct_predicate, unstruct_hook)

        if struct_hook is not None:
            converter.register_structure_hook_func(cls_is_cl, struct_hook)
