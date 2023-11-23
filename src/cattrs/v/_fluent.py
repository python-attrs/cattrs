"""The fluent validation API."""
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Collection,
    Generic,
    Iterable,
    Literal,
    Sequence,
    Sized,
    TypeVar,
)

try:
    from typing import assert_never
except ImportError:
    from typing_extensions import assert_never

from attrs import Attribute, AttrsInstance, define
from attrs import fields as f

from cattrs import BaseConverter
from cattrs._compat import ExceptionGroup
from cattrs.dispatch import StructureHook
from cattrs.gen import make_dict_structure_fn, override

T = TypeVar("T")


@define
class VOmitted:
    """This attribute has been marked for omission.

    The class contains no methods.
    """

    attr: Attribute[Any]


@define
class VRenamed(Generic[T]):
    """This attribute has been renamed.

    This class has no `omit` and no `rename`..
    """

    attr: Attribute[T]
    new_name: str

    def ensure(
        self: VRenamed[T],
        validator: Callable[[T], None | bool],
        *validators: Callable[[T], None | bool],
    ) -> VCustomized[T]:
        return VCustomized(self.attr, self.new_name, (validator, *validators))


@define
class VCustomized(Generic[T]):
    """This attribute has been customized.

    This class has no `omit`.
    """

    attr: Attribute[T]
    new_name: str | None
    hooks: tuple[Callable[[T], None | bool], ...] = ()


@define
class V(Generic[T]):
    """
    The cattrs.v validation attribute.

    Instances are initialized from `attrs.Attribute`s.

    One V attribute maps directly to each class attribute.


    """

    def __init__(self, attr: Attribute[T]) -> None:
        self.attr = attr
        self.hooks = ()

    attr: Attribute[T]
    hooks: tuple[Callable[[T], None], ...] = ()

    def ensure(
        self: V[T],
        validator: Callable[[T], None | bool],
        *validators: Callable[[T], None],
    ) -> VCustomized[T]:
        hooks = (*self.hooks, validator, *validators)
        return VCustomized(self.attr, None, hooks)

    def rename(self: V[T], new_name: str) -> VRenamed[T]:
        """Rename the attribute after processing."""
        return VRenamed(self.attr, new_name)

    def omit(self) -> VOmitted:
        """Omit the attribute."""
        return VOmitted(self.attr)

    def replace_with(self, value: T) -> VOmitted:
        """This attribute should be replaced with a value when structuring."""
        return VOmitted(self.attr)


def is_unique(val: Collection[Any]) -> None:
    """Ensure all elements in a collection are unique.

    Takes a value that implements Collection.
    """
    if len(val) != len(set(val)):
        raise ValueError(f"Value ({val}) not unique")


def len_between(min: int, max: int) -> Callable[[Sized], None]:
    """Ensure the length of the argument is between min (inclusive) and max (exclusive)."""

    def assert_len_between(val: Sized, _min: int = min, _max: int = max) -> None:
        length = len(val)
        if not (_min <= length < max):
            raise ValueError(f"Length ({length}) not between {_min} and {_max}")

    return assert_len_between


def ignoring_none(*validators: Callable[[T], None]) -> Callable[[T | None], None]:
    """
    A validator for (f.e.) strings cannot be applied to `str | None`, but it can
    be wrapped with this to adapt it so it can.
    """

    def skip_none(val: T | None) -> None:
        if val is None:
            return
        errors = []
        for validator in validators:
            try:
                validator(val)
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise ExceptionGroup("", errors)

    return skip_none


def all_elements_must(
    validator: Callable[[T], None | bool], *validators: Callable[[T], None | bool]
) -> Callable[[Iterable[T]], None | bool]:
    """A helper validator included with cattrs.

    Run all the given validators against all members of the
    iterable.
    """

    validators = (validator, *validators)

    def assert_all_elements(val: Iterable[T]) -> None:
        errors = []
        for e in val:
            for v in validators:
                try:
                    v(e)
                except Exception as exc:
                    errors.append(exc)
        if errors:
            raise ExceptionGroup("", errors)

    return assert_all_elements


def _compose_validators(
    base_structure: StructureHook,
    validators: Sequence[Callable[[Any], None | bool]],
    detailed_validation: bool,
) -> Callable[[Any, Any], Any]:
    """Produce a hook composing the base structuring hook and additional validators.

    The validators will run only if the base structuring succeeds; no point otherwise.

    The new hook will raise an ExceptionGroup.
    """
    bs = base_structure

    if detailed_validation:

        def structure_hook(
            val: dict[str, Any], t: Any, _hooks=validators, _bs=bs
        ) -> Any:
            res = _bs(val, t)
            errors: list[Exception] = []
            for hook in _hooks:
                try:
                    hook(val)
                except Exception as exc:
                    errors.append(exc)
            if errors:
                raise ExceptionGroup("Validation errors structuring {}", errors)
            return res

    else:

        def structure_hook(
            val: dict[str, Any], t: Any, _hooks=validators, _bs=bs
        ) -> Any:
            res = _bs(val, t)
            for hook in _hooks:
                hook(val)
            return res

    return structure_hook


def customize(
    converter: BaseConverter,
    cl: type[AttrsInstance],
    *fields: VCustomized[Any] | VRenamed[Any] | VOmitted,
    detailed_validation: bool | Literal["from_converter"] = "from_converter",
    forbid_extra_keys: bool | Literal["from_converter"] = "from_converter",
) -> StructureHook:
    """Customize the structuring process for an attrs class.

    :param converter: The converter to fetch subhooks from, and to which the
        customization will be applied to.
    :param cl: The _attrs_ class to be customized.
    :param fields: The fields to apply customizations to.
    :param detailed_validation: Whether to enable detailed validation.
    :param forbid_extra_keys: Whether to check for extra keys when structuring.

    ..  versionadded:: 24.1.0
    """
    seen = set()
    overrides = {}
    if detailed_validation == "from_converter":
        detailed_validation = converter.detailed_validation
    for field in fields:
        if field.attr.name in seen:
            raise Exception(f"Duplicate customization for field {field.attr.name}")
        if field.attr is not getattr(f(cl), field.attr.name):
            raise TypeError(f"Customizing {cl}, but {field} is from a different class")
        seen.add(field.attr.name)
        if isinstance(field, VOmitted):
            overrides[field.attr.name] = override(omit=True)
        elif isinstance(field, VRenamed):
            overrides[field.attr.name] = override(rename=field.new_name)
        elif isinstance(field, VCustomized):
            base_hook = converter._structure_func.dispatch(field.attr.type)
            hook = _compose_validators(base_hook, field.hooks, detailed_validation)
            overrides[field.attr.name] = override(
                rename=field.new_name, struct_hook=hook
            )
        else:
            # The match is exhaustive.
            assert_never(field)
    res = make_dict_structure_fn(
        cl,
        converter,
        _cattrs_detailed_validation=detailed_validation,
        _cattrs_forbid_extra_keys=forbid_extra_keys,
        **overrides,
    )
    converter.register_structure_hook(cl, res)
    return res
