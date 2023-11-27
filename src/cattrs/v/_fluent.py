"""The fluent validation API."""
from __future__ import annotations

from typing import Any, Callable, Generic, Literal, Sequence, TypeVar

try:
    from typing import assert_never
except ImportError:
    from typing_extensions import assert_never

try:
    from typing import TypeGuard
except ImportError:
    from typing_extensions import TypeGuard

from inspect import signature

from attrs import Attribute, AttrsInstance, define
from attrs import fields as f

from .. import BaseConverter
from .._compat import ExceptionGroup, TypeAlias
from ..dispatch import StructureHook
from ..gen import make_dict_structure_fn, override

T = TypeVar("T")

ValidatorFactory: TypeAlias = Callable[[bool], Callable[[T], None]]


@define
class VOmitted:
    """This attribute has been marked for omission.

    The class contains no methods.
    """

    attr: Attribute[Any]


@define
class VRenamed(Generic[T]):
    """This attribute has been renamed.

    This class has no `omit` and no `rename`.
    """

    attr: Attribute[T]
    new_name: str

    def ensure(
        self: VRenamed[T],
        validator: Callable[[T], None | bool] | ValidatorFactory[T],
        *validators: Callable[[T], None | bool] | ValidatorFactory[T],
    ) -> VCustomized[T]:
        return VCustomized(self.attr, self.new_name, (validator, *validators))


@define
class VCustomized(Generic[T]):
    """This attribute has been customized.

    This class has no `omit`.
    """

    attr: Attribute[T]
    new_name: str | None
    validators: tuple[Callable[[T], None | bool] | ValidatorFactory[T], ...] = ()


@define
class V(Generic[T]):
    """
    The cattrs.v validation attribute.

    Instances are initialized from `attrs.Attribute`s.

    One V attribute maps directly to each class attribute.


    """

    def __init__(self, attr: Attribute[T]) -> None:
        self.attr = attr
        self.validators = ()

    attr: Attribute[T]
    validators: tuple[Callable[[T], None | bool] | ValidatorFactory[T], ...] = ()

    def ensure(
        self: V[T],
        validator: Callable[[T], None | bool] | ValidatorFactory[T],
        *validators: Callable[[T], None] | ValidatorFactory[T],
    ) -> VCustomized[T]:
        return VCustomized(self.attr, None, (*self.validators, validator, *validators))

    def rename(self: V[T], new_name: str) -> VRenamed[T]:
        """Rename the attribute after processing."""
        return VRenamed(self.attr, new_name)

    def omit(self) -> VOmitted:
        """Omit the attribute."""
        return VOmitted(self.attr)


def _is_validator_factory(
    validator: Callable[[Any], None | bool] | ValidatorFactory[T]
) -> TypeGuard[ValidatorFactory[T]]:
    """Figure out if this is a validator factory or not."""
    sig = signature(validator)
    ra = sig.return_annotation
    return (
        callable(ra)
        or isinstance(ra, str)
        and sig.return_annotation.startswith("Callable")
    )


def _compose_validators(
    base_structure: StructureHook,
    validators: Sequence[Callable[[Any], None | bool] | ValidatorFactory],
    detailed_validation: bool,
) -> Callable[[Any, Any], Any]:
    """Produce a hook composing the base structuring hook and additional validators.

    The validators will run only if the base structuring succeeds; no point otherwise.

    The new hook will raise an ExceptionGroup.
    """
    bs = base_structure
    final_validators = []
    for val in validators:
        if _is_validator_factory(val):
            final_validators.append(val(detailed_validation))
        else:
            final_validators.append(val)

    if detailed_validation:

        def structure_hook(
            val: dict[str, Any], t: Any, _hooks=final_validators, _bs=bs
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
            val: dict[str, Any], t: Any, _hooks=final_validators, _bs=bs
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
            raise TypeError(f"Duplicate customization for field {field.attr.name}")
        if field.attr is not getattr(f(cl), field.attr.name):
            raise TypeError(f"Customizing {cl}, but {field} is from a different class")
        seen.add(field.attr.name)
        if isinstance(field, VOmitted):
            overrides[field.attr.name] = override(omit=True)
        elif isinstance(field, VRenamed):
            overrides[field.attr.name] = override(rename=field.new_name)
        elif isinstance(field, VCustomized):
            base_hook = converter._structure_func.dispatch(field.attr.type)
            hook = _compose_validators(base_hook, field.validators, detailed_validation)
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
