"""Strategies for typed dicts."""
from datetime import datetime
from string import ascii_lowercase
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar

from attr import NOTHING
from hypothesis.strategies import (
    DrawFn,
    SearchStrategy,
    booleans,
    composite,
    datetimes,
    integers,
    just,
    lists,
    sets,
    text,
)

from cattrs._compat import ExtensionsTypedDict, NotRequired, Required, TypedDict

from .untyped import gen_attr_names

# Type aliases for readability
TypedDictType = type
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")


def gen_typeddict_attr_names():
    """Typed dicts can have periods in their field names."""
    counter = 0
    for n in gen_attr_names():
        counter += 1

        if counter % 2 == 0:
            n = f"{n}.suffix"

        yield n


@composite
def int_attributes(
    draw: DrawFn, total: bool = True, not_required: bool = False
) -> Tuple[int, SearchStrategy, SearchStrategy]:
    if total:
        if not_required and draw(booleans()):
            return (NotRequired[int], integers() | just(NOTHING), text(ascii_lowercase))
        return int, integers(), text(ascii_lowercase)

    if not_required and draw(booleans()):
        return Required[int], integers(), text(ascii_lowercase)

    return int, integers() | just(NOTHING), text(ascii_lowercase)


@composite
def datetime_attributes(
    draw: DrawFn, total: bool = True, not_required: bool = False
) -> Tuple[datetime, SearchStrategy, SearchStrategy]:
    success_strat = datetimes(
        min_value=datetime(1970, 1, 1), max_value=datetime(2038, 1, 1)
    ).map(lambda dt: dt.replace(microsecond=0))
    type = datetime
    strat = success_strat if total else success_strat | just(NOTHING)
    if not_required and draw(booleans()):
        if total:
            type = NotRequired[type]
            strat = success_strat | just(NOTHING)
        else:
            type = Required[type]
            strat = success_strat
    return (type, strat, text(ascii_lowercase))


@composite
def list_of_int_attributes(
    draw: DrawFn, total: bool = True, not_required: bool = False
) -> Tuple[List[int], SearchStrategy, SearchStrategy]:
    if total:
        if not_required and draw(booleans()):
            return (
                NotRequired[List[int]],
                lists(integers()) | just(NOTHING),
                text(ascii_lowercase).map(lambda v: [v]),
            )

        return (List[int], lists(integers()), text(ascii_lowercase).map(lambda v: [v]))

    if not_required and draw(booleans()):
        return (
            Required[List[int]],
            lists(integers()),
            text(ascii_lowercase).map(lambda v: [v]),
        )

    return (
        List[int],
        lists(integers()) | just(NOTHING),
        text(ascii_lowercase).map(lambda v: [v]),
    )


@composite
def simple_typeddicts(
    draw: DrawFn,
    total: Optional[bool] = None,
    not_required: bool = False,
    min_attrs: int = 0,
    typeddict_cls: Optional[Any] = None,
) -> Tuple[TypedDictType, dict]:
    """Generate simple typed dicts.

    :param total: Generate the given totality dicts (default = random)
    """
    if total is None:
        total = draw(booleans())

    attrs = draw(
        lists(
            int_attributes(total, not_required)
            | list_of_int_attributes(total, not_required)
            | datetime_attributes(total, not_required),
            min_size=min_attrs,
        )
    )

    attrs_dict = {n: attr[0] for n, attr in zip(gen_typeddict_attr_names(), attrs)}
    success_payload = {}
    for n, a in zip(attrs_dict, attrs):
        v = draw(a[1])
        if v is not NOTHING:
            success_payload[n] = v

    cls = (
        (TypedDict if draw(booleans()) else ExtensionsTypedDict)
        if typeddict_cls is None
        else typeddict_cls
    )("HypTypedDict", attrs_dict, total=total)

    if draw(booleans()):

        class InheritedTypedDict(cls):
            inherited: int

        cls = InheritedTypedDict
        success_payload["inherited"] = draw(integers())

    return (cls, success_payload)


@composite
def simple_typeddicts_with_extra_keys(
    draw: DrawFn, total: Optional[bool] = None, typeddict_cls: Optional[Any] = None
) -> Tuple[TypedDictType, dict, Set[str]]:
    """Generate TypedDicts, with the instances having extra keys."""
    cls, success = draw(simple_typeddicts(total, typeddict_cls=typeddict_cls))

    # The normal attributes are 2 characters or less.
    extra_keys = draw(sets(text(ascii_lowercase, min_size=3, max_size=3)))
    success.update({k: 1 for k in extra_keys})

    return cls, success, extra_keys


@composite
def generic_typeddicts(
    draw: DrawFn, total: Optional[bool] = None
) -> Tuple[TypedDictType, dict]:
    """Generate generic typed dicts.

    :param total: Generate the given totality dicts (default = random)
    """
    if total is None:
        total = draw(booleans())

    attrs = draw(
        lists(
            int_attributes(total)
            | list_of_int_attributes(total)
            | datetime_attributes(total),
            min_size=1,
        )
    )

    attrs_dict = {n: attr[0] for n, attr in zip(gen_attr_names(), attrs)}
    success_payload = {}
    for n, a in zip(attrs_dict, attrs):
        v = draw(a[1])
        if v is not NOTHING:
            success_payload[n] = v

    # We choose up to 3 attributes and make them generic.
    generic_attrs = draw(
        lists(integers(0, len(attrs) - 1), min_size=1, max_size=3, unique=True)
    )
    generics = []
    actual_types = []
    for ix, (attr_name, attr_type) in enumerate(list(attrs_dict.items())):
        if ix in generic_attrs:
            typevar = TypeVar(f"T{ix+1}")
            generics.append(typevar)
            actual_types.append(attr_type)
            attrs_dict[attr_name] = typevar

    cls = make_typeddict(
        "HypTypedDict", attrs_dict, total=total, bases=[Generic[tuple(generics)]]
    )

    if draw(booleans()):

        class InheritedTypedDict(cls[tuple(actual_types)]):
            inherited: int

        cls = InheritedTypedDict
        success_payload["inherited"] = draw(integers())
    else:
        cls = cls[tuple(actual_types)]

    return (cls, success_payload)


def make_typeddict(
    cls_name: str, attrs: Dict[str, type], total: bool = True, bases: List = []
) -> TypedDictType:
    globs = {"TypedDict": TypedDict}
    lines = []

    bases_snippet = ",".join(f"_base{ix}" for ix in range(len(bases)))
    for ix, base in enumerate(bases):
        globs[f"_base{ix}"] = base
    if bases_snippet:
        bases_snippet = f", {bases_snippet}"

    lines.append(f"class {cls_name}(TypedDict{bases_snippet},total={total}):")
    for n, t in attrs.items():
        # Strip the initial underscore if present, to prevent mangling.
        trimmed = n[1:] if n.startswith("_") else n
        globs[f"_{trimmed}_type"] = t
        lines.append(f"  {n}: _{trimmed}_type")

    script = "\n".join(lines)
    eval(compile(script, "name", "exec"), globs)

    return globs[cls_name]
