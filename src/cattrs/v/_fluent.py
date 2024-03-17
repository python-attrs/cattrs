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
from .._compat import ExceptionGroup, fields_dict, get_origin
from .._types import DataclassLike
from ..dispatch import StructureHook
from ..gen import make_dict_structure_fn, override
from ._types import Validator, ValidatorFactory
from .fns import invalid_value

T = TypeVar("T")


@define
class VOmitted:
    """This attribute has been marked for omission.

    The class contains no methods.
    """

    attr: str


@define
class VRenamed(Generic[T]):
    """This attribute has been renamed.

    This class has no `omit` and no `rename`.
    """

    attr: Attribute[T] | str
    new_name: str

    def ensure(
        self: VRenamed[T],
        validator: Validator[T] | ValidatorFactory[T],
        *validators: Validator[T] | ValidatorFactory[T],
    ) -> VCustomized[T]:
        return VCustomized(
            self.attr if isinstance(self.attr, str) else self.attr.name,
            self.new_name,
            (validator, *validators),
        )


@define
class VCustomized(Generic[T]):
    """This attribute has been customized.

    This class has no `omit`.
    """

    attr: str
    new_name: str | None
    validators: tuple[Callable[[T], None | bool] | ValidatorFactory[T], ...] = ()


@define
class V(Generic[T]):
    """
    The cattrs.v validation attribute.

    Instances are initialized from strings or `attrs.Attribute`s.

    One V attribute maps directly to each class attribute.
    """

    def __init__(self, attr: Attribute[T] | str) -> None:
        self.attr = attr
        self.validators = ()

    attr: Attribute[T] | str
    validators: tuple[Callable[[T], None | bool] | ValidatorFactory[T], ...] = ()

    def ensure(
        self: V[T],
        validator: Validator[T] | ValidatorFactory[T],
        *validators: Validator[T] | ValidatorFactory[T],
    ) -> VCustomized[T]:
        return VCustomized(self.attr, None, (*self.validators, validator, *validators))

    def rename(self: V[T], new_name: str) -> VRenamed[T]:
        """Rename the attribute after processing."""
        return VRenamed(self.attr, new_name)

    def omit(self) -> VOmitted:
        """Omit the attribute."""
        return VOmitted(self.attr if isinstance(self.attr, str) else self.attr.name)


def _is_validator_factory(
    validator: Callable[[Any], None | bool] | ValidatorFactory[T]
) -> TypeGuard[ValidatorFactory[T]]:
    """Figure out if this is a validator factory or not."""
    sig = signature(validator)
    ra = sig.return_annotation
    return (
        ra.startswith("Validator")
        if isinstance(ra, str)
        else get_origin(ra) is Validator
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
                    if hook(val) is False:
                        invalid_value(val)
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
                if hook(val) is False:
                    invalid_value(val)
            return res

    return structure_hook


def customize(
    converter: BaseConverter,
    cl: type[AttrsInstance] | type[DataclassLike],
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
        field_name = field.attr if isinstance(field.attr, str) else field.attr.name
        if field_name in seen:
            raise TypeError(f"Duplicate customization for field {field_name}")

        if isinstance(field.attr, str):
            try:
                attribute = fields_dict(cl)[field.attr]
            except KeyError:
                raise TypeError(f"Class {cl} has no field {field}") from None
        else:
            attribute = field.attr

        if not isinstance(field.attr, str) and field.attr is not getattr(
            f(cl), field.attr.name
        ):
            raise TypeError(f"Customizing {cl}, but {field} is from a different class")
        seen.add(field_name)
        if isinstance(field, VOmitted):
            overrides[field_name] = override(omit=True)
        elif isinstance(field, VRenamed):
            overrides[field_name] = override(rename=field.new_name)
        elif isinstance(field, VCustomized):
            base_hook = converter._structure_func.dispatch(attribute.type)
            hook = _compose_validators(base_hook, field.validators, detailed_validation)
            overrides[field_name] = override(rename=field.new_name, struct_hook=hook)
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
