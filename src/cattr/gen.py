import re
from typing import Optional, Type, TypeVar

import attr
from attr import NOTHING, resolve_types

from cattr._compat import get_args, get_origin, is_generic


@attr.s(slots=True, frozen=True)
class AttributeOverride(object):
    omit_if_default: Optional[bool] = attr.ib(default=None)
    rename: Optional[str] = attr.ib(default=None)


def override(omit_if_default=None, rename=None):
    return AttributeOverride(omit_if_default=omit_if_default, rename=rename)


_neutral = AttributeOverride()


def make_dict_unstructure_fn(cl, converter, omit_if_default=False, **kwargs):
    """Generate a specialized dict unstructuring function for an attrs class."""
    cl_name = cl.__name__
    fn_name = "unstructure_" + cl_name
    globs = {"__c_u": converter.unstructure}
    lines = []
    post_lines = []

    attrs = cl.__attrs_attrs__  # type: ignore

    lines.append(f"def {fn_name}(i):")
    lines.append("    res = {")
    for a in attrs:
        attr_name = a.name
        override = kwargs.pop(attr_name, _neutral)
        kn = attr_name if override.rename is None else override.rename
        d = a.default
        if d is not attr.NOTHING and (
            (omit_if_default and override.omit_if_default is not False)
            or override.omit_if_default
        ):
            def_name = f"__cattr_def_{attr_name}"

            if isinstance(d, attr.Factory):
                globs[def_name] = d.factory
                if d.takes_self:
                    post_lines.append(
                        f"    if i.{attr_name} != {def_name}(i):"
                    )
                else:
                    post_lines.append(f"    if i.{attr_name} != {def_name}():")
                post_lines.append(f"        res['{kn}'] = i.{attr_name}")
            else:
                globs[def_name] = d
                post_lines.append(f"    if i.{attr_name} != {def_name}:")
                post_lines.append(
                    f"        res['{kn}'] = __c_u(i.{attr_name})"
                )

        else:
            # No default or no override.
            lines.append(f"        '{kn}': __c_u(i.{attr_name}),")
    lines.append("    }")

    total_lines = lines + post_lines + ["    return res"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    fn = globs[fn_name]

    return fn


def generate_mapping(cl: Type, old_mapping):
    mapping = {}
    for p, t in zip(get_origin(cl).__parameters__, get_args(cl)):
        if isinstance(t, TypeVar):
            continue
        mapping[p.__name__] = t

    if not mapping:
        return old_mapping

    cls = attr.make_class(
        "GenericMapping",
        {x: attr.attrib() for x in mapping.keys()},
        frozen=True,
    )

    return cls(**mapping)


def make_dict_structure_fn(cl: Type, converter, **kwargs):
    """Generate a specialized dict structuring function for an attrs class."""

    mapping = None
    if is_generic(cl):
        base = get_origin(cl)
        mapping = generate_mapping(cl, mapping)
        cl = base

    for base in getattr(cl, "__orig_bases__", ()):
        if is_generic(base) and not str(base).startswith("typing.Generic"):
            mapping = generate_mapping(base, mapping)
            break

    if isinstance(cl, TypeVar):
        cl = getattr(mapping, cl.__name__, cl)

    cl_name = cl.__name__
    fn_name = "structure_" + cl_name

    # We have generic paramters and need to generate a unique name for the function
    for p in getattr(cl, "__parameters__", ()):
        # This is nasty, I am not sure how best to handle `typing.List[str]` or `TClass[int, int]` as a parameter type here
        name_base = getattr(mapping, p.__name__)
        name = getattr(name_base, "__name__", str(name_base))
        name = re.sub(r"[\[\.\] ,]", "_", name)
        fn_name += f"_{name}"

    globs = {"__c_s": converter.structure, "__cl": cl, "__m": mapping}
    lines = []
    post_lines = []

    attrs = cl.__attrs_attrs__

    if any(isinstance(a.type, str) for a in attrs):
        # PEP 563 annotations - need to be resolved.
        resolve_types(cl)

    lines.append(f"def {fn_name}(o, *_):")
    lines.append("  res = {")
    for a in attrs:
        an = a.name
        override = kwargs.pop(an, _neutral)
        type = a.type
        if isinstance(type, TypeVar):
            type = getattr(mapping, type.__name__, type)

        ian = an if an[0] != "_" else an[1:]
        kn = an if override.rename is None else override.rename
        globs[f"__c_t_{an}"] = type
        if a.default is NOTHING:
            lines.append(f"    '{ian}': __c_s(o['{kn}'], __c_t_{an}),")
        else:
            post_lines.append(f"  if '{kn}' in o:")
            post_lines.append(
                f"    res['{ian}'] = __c_s(o['{kn}'], __c_t_{an})"
            )
    lines.append("    }")

    total_lines = lines + post_lines + ["  return __cl(**res)"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    return globs[fn_name]
