import linecache
import re
import uuid
from dataclasses import is_dataclass
from threading import local
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

import attr
from attr import NOTHING, resolve_types

from ._compat import adapted_fields, get_args, get_origin, is_bare, is_generic

if TYPE_CHECKING:  # pragma: no cover
    from cattr.converters import Converter


@attr.s(slots=True, frozen=True)
class AttributeOverride:
    omit_if_default: Optional[bool] = attr.ib(default=None)
    rename: Optional[str] = attr.ib(default=None)
    omit: bool = attr.ib(default=False)  # Omit the field completely.


def override(omit_if_default=None, rename=None, omit: bool = False):
    return AttributeOverride(
        omit_if_default=omit_if_default, rename=rename, omit=omit
    )


_neutral = AttributeOverride()
_already_generating = local()


def make_dict_unstructure_fn(
    cl,
    converter,
    omit_if_default: bool = False,
    _cattrs_use_linecache: bool = True,
    **kwargs,
):
    """Generate a specialized dict unstructuring function for an attrs class."""
    cl_name = cl.__name__
    fn_name = "unstructure_" + cl_name
    globs = {}
    lines = []
    post_lines = []

    attrs = adapted_fields(cl)  # type: ignore

    # We keep track of what we're generating to help with recursive
    # class graphs.
    try:
        working_set = _already_generating.working_set
    except AttributeError:
        working_set = set()
        _already_generating.working_set = working_set
    if cl in working_set:
        raise RecursionError()
    else:
        working_set.add(cl)
    try:
        lines.append(f"def {fn_name}(instance):")
        lines.append("    res = {")
        for a in attrs:
            attr_name = a.name
            override = kwargs.pop(attr_name, _neutral)
            if override.omit:
                continue
            kn = attr_name if override.rename is None else override.rename
            d = a.default

            # For each attribute, we try resolving the type here and now.
            # If a type is manually overwritten, this function should be
            # regenerated.
            if a.type is not None:
                try:
                    handler = converter._unstructure_func.dispatch(a.type)
                except RecursionError:
                    # There's a circular reference somewhere down the line
                    handler = converter.unstructure
            else:
                handler = converter.unstructure

            is_identity = handler == converter._unstructure_identity

            if not is_identity:
                unstruct_handler_name = f"unstructure_{attr_name}"
                globs[unstruct_handler_name] = handler
                invoke = f"{unstruct_handler_name}(instance.{attr_name})"
            else:
                invoke = f"instance.{attr_name}"

            if d is not attr.NOTHING and (
                (omit_if_default and override.omit_if_default is not False)
                or override.omit_if_default
            ):
                def_name = f"__cattr_def_{attr_name}"

                if isinstance(d, attr.Factory):
                    globs[def_name] = d.factory
                    if d.takes_self:
                        post_lines.append(
                            f"    if instance.{attr_name} != {def_name}(instance):"
                        )
                    else:
                        post_lines.append(
                            f"    if instance.{attr_name} != {def_name}():"
                        )
                    post_lines.append(f"        res['{kn}'] = {invoke}")
                else:
                    globs[def_name] = d
                    post_lines.append(
                        f"    if instance.{attr_name} != {def_name}:"
                    )
                    post_lines.append(f"        res['{kn}'] = {invoke}")

            else:
                # No default or no override.
                lines.append(f"        '{kn}': {invoke},")
        lines.append("    }")

        total_lines = lines + post_lines + ["    return res"]
        script = "\n".join(total_lines)

        fname = _generate_unique_filename(
            cl, "unstructure", reserve=_cattrs_use_linecache
        )

        eval(compile(script, fname, "exec"), globs)

        fn = globs[fn_name]
        if _cattrs_use_linecache:
            linecache.cache[fname] = len(script), None, total_lines, fname
    finally:
        working_set.remove(cl)

    return fn


def _generate_mapping(cl: Type, old_mapping):
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


def make_dict_structure_fn(
    cl: Type,
    converter: "Converter",
    _cattrs_forbid_extra_keys: bool = False,
    _cattrs_use_linecache: bool = True,
    _cattrs_prefer_attrib_converters: bool = False,
    **kwargs,
):
    """Generate a specialized dict structuring function for an attrs class."""

    mapping = None
    if is_generic(cl):
        base = get_origin(cl)
        mapping = _generate_mapping(cl, mapping)
        cl = base

    for base in getattr(cl, "__orig_bases__", ()):
        if is_generic(base) and not str(base).startswith("typing.Generic"):
            mapping = _generate_mapping(base, mapping)
            break

    if isinstance(cl, TypeVar):
        cl = getattr(mapping, cl.__name__, cl)

    cl_name = cl.__name__
    fn_name = "structure_" + cl_name

    # We have generic parameters and need to generate a unique name for the function
    for p in getattr(cl, "__parameters__", ()):
        # This is nasty, I am not sure how best to handle `typing.List[str]` or `TClass[int, int]` as a parameter type here
        name_base = getattr(mapping, p.__name__)
        name = getattr(name_base, "__name__", str(name_base))
        name = re.sub(r"[\[\.\] ,]", "_", name)
        fn_name += f"_{name}"

    globs = {"__c_s": converter.structure, "__cl": cl, "__m": mapping}
    lines = []
    post_lines = []

    attrs = adapted_fields(cl)
    is_dc = is_dataclass(cl)

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

        # For each attribute, we try resolving the type here and now.
        # If a type is manually overwritten, this function should be
        # regenerated.
        if a.converter is not None and _cattrs_prefer_attrib_converters:
            handler = None
        elif (
            a.converter is not None
            and not _cattrs_prefer_attrib_converters
            and type is not None
        ):
            handler = converter._structure_func.dispatch(type)
            if handler == converter._structure_error:
                handler = None
        elif type is not None:
            handler = converter._structure_func.dispatch(type)
        else:
            handler = converter.structure

        struct_handler_name = f"structure_{an}"
        globs[struct_handler_name] = handler

        ian = an if (is_dc or an[0] != "_") else an[1:]
        kn = an if override.rename is None else override.rename
        globs[f"type_{an}"] = type
        if a.default is NOTHING:
            if handler:
                lines.append(
                    f"    '{ian}': {struct_handler_name}(o['{kn}'], type_{an}),"
                )
            else:
                lines.append(f"    '{ian}': o['{kn}'],")
        else:
            post_lines.append(f"  if '{kn}' in o:")
            if handler:
                post_lines.append(
                    f"    res['{ian}'] = {struct_handler_name}(o['{kn}'], type_{an})"
                )
            else:
                post_lines.append(f"    res['{ian}'] = o['{kn}']")

    lines.append("    }")
    if _cattrs_forbid_extra_keys:
        allowed_fields = {a.name for a in attrs}
        globs["__c_a"] = allowed_fields
        post_lines += [
            "  unknown_fields = set(o.keys()) - __c_a",
            "  if unknown_fields:",
            "    raise Exception(",
            f"      'Extra fields in constructor for {cl_name}: ' + ', '.join(unknown_fields)"
            "    )",
        ]

    total_lines = lines + post_lines + ["  return __cl(**res)"]

    fname = _generate_unique_filename(
        cl, "structure", reserve=_cattrs_use_linecache
    )
    script = "\n".join(total_lines)
    eval(compile(script, fname, "exec"), globs)
    if _cattrs_use_linecache:
        linecache.cache[fname] = len(script), None, total_lines, fname

    return globs[fn_name]


def make_iterable_unstructure_fn(cl: Any, converter, unstructure_to=None):
    """Generate a specialized unstructure function for an iterable."""
    handler = converter.unstructure

    fn_name = "unstructure_iterable"

    # Let's try fishing out the type args.
    if getattr(cl, "__args__", None) is not None:
        type_arg = get_args(cl)[0]
        # We can do the dispatch here and now.
        handler = converter._unstructure_func.dispatch(type_arg)

    globs = {"__cattr_seq_cl": unstructure_to or cl, "__cattr_u": handler}
    lines = []

    lines.append(f"def {fn_name}(iterable):")
    lines.append("    res = __cattr_seq_cl(__cattr_u(i) for i in iterable)")

    total_lines = lines + ["    return res"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    fn = globs[fn_name]

    return fn


def make_hetero_tuple_unstructure_fn(cl: Any, converter, unstructure_to=None):
    """Generate a specialized unstructure function for a heterogenous tuple."""
    fn_name = "unstructure_tuple"

    type_args = get_args(cl)

    # We can do the dispatch here and now.
    handlers = [
        converter._unstructure_func.dispatch(type_arg)
        for type_arg in type_args
    ]

    globs = {f"__cattr_u_{i}": h for i, h in enumerate(handlers)}
    if unstructure_to is not tuple:
        globs["__cattr_seq_cl"] = unstructure_to or cl
    lines = []

    lines.append(f"def {fn_name}(tup):")
    if unstructure_to is not tuple:
        lines.append("    res = __cattr_seq_cl((")
    else:
        lines.append("    res = (")
    for i in range(len(handlers)):
        if handlers[i] == converter._unstructure_identity:
            lines.append(f"        tup[{i}],")
        else:
            lines.append(f"        __cattr_u_{i}(tup[{i}]),")

    if unstructure_to is not tuple:
        lines.append("    ))")
    else:
        lines.append("    )")

    total_lines = lines + ["    return res"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    fn = globs[fn_name]

    return fn


def make_mapping_unstructure_fn(
    cl: Any, converter, unstructure_to=None, key_handler=None
):
    """Generate a specialized unstructure function for a mapping."""
    kh = key_handler or converter.unstructure
    val_handler = converter.unstructure

    fn_name = "unstructure_mapping"

    # Let's try fishing out the type args.
    if getattr(cl, "__args__", None) is not None:
        args = get_args(cl)
        if len(args) == 2:
            key_arg, val_arg = args
        else:
            # Probably a Counter
            key_arg, val_arg = args, Any
        # We can do the dispatch here and now.
        kh = key_handler or converter._unstructure_func.dispatch(key_arg)
        if kh == converter._unstructure_identity:
            kh = None

        val_handler = converter._unstructure_func.dispatch(val_arg)
        if val_handler == converter._unstructure_identity:
            val_handler = None

    globs = {
        "__cattr_mapping_cl": unstructure_to or cl,
        "__cattr_k_u": kh,
        "__cattr_v_u": val_handler,
    }

    k_u = "__cattr_k_u(k)" if kh is not None else "k"
    v_u = "__cattr_v_u(v)" if val_handler is not None else "v"

    lines = []

    lines.append(f"def {fn_name}(mapping):")
    lines.append(
        f"    res = __cattr_mapping_cl(({k_u}, {v_u}) for k, v in mapping.items())"
    )

    total_lines = lines + ["    return res"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    fn = globs[fn_name]

    return fn


def make_mapping_structure_fn(
    cl: Any, converter, structure_to=dict, key_type=NOTHING, val_type=NOTHING
):
    """Generate a specialized unstructure function for a mapping."""
    fn_name = "structure_mapping"

    globs = {"__cattr_mapping_cl": structure_to}

    lines = []
    lines.append(f"def {fn_name}(mapping, _):")

    # Let's try fishing out the type args.
    if not is_bare(cl):
        args = get_args(cl)
        if len(args) == 2:
            key_arg_cand, val_arg_cand = args
            if key_type is NOTHING:
                key_type = key_arg_cand
            if val_type is NOTHING:
                val_type = val_arg_cand
        else:
            if key_type is not NOTHING and val_type is NOTHING:
                (val_type,) = args
            elif key_type is NOTHING and val_type is not NOTHING:
                (key_type,) = args
            else:
                # Probably a Counter
                (key_type,) = args
                val_type = Any

        is_bare_dict = val_type is Any and key_type is Any
        if not is_bare_dict:
            # We can do the dispatch here and now.
            key_handler = converter._structure_func.dispatch(key_type)
            if key_handler == converter._structure_call:
                key_handler = key_type

            val_handler = converter._structure_func.dispatch(val_type)
            if val_handler == converter._structure_call:
                val_handler = val_type

            globs["__cattr_k_t"] = key_type
            globs["__cattr_v_t"] = val_type
            globs["__cattr_k_s"] = key_handler
            globs["__cattr_v_s"] = val_handler
            k_s = (
                "__cattr_k_s(k, __cattr_k_t)"
                if key_handler != key_type
                else "__cattr_k_s(k)"
            )
            v_s = (
                "__cattr_v_s(v, __cattr_v_t)"
                if val_handler != val_type
                else "__cattr_v_s(v)"
            )
    else:
        is_bare_dict = True

    if is_bare_dict:
        # No args, it's a bare dict.
        lines.append("    res = dict(mapping)")
    else:
        lines.append(f"    res = {{{k_s}: {v_s} for k, v in mapping.items()}}")
    if structure_to is not dict:
        lines.append("    res = __cattr_mapping_cl(res)")

    total_lines = lines + ["    return res"]

    eval(compile("\n".join(total_lines), "", "exec"), globs)

    fn = globs[fn_name]

    return fn


def _generate_unique_filename(cls, func_name, reserve=True):
    """
    Create a "filename" suitable for a function being generated.
    """
    unique_id = uuid.uuid4()
    extra = ""
    count = 1

    while True:
        unique_filename = "<cattrs generated {0} {1}.{2}{3}>".format(
            func_name,
            cls.__module__,
            getattr(cls, "__qualname__", cls.__name__),
            extra,
        )
        if not reserve:
            return unique_filename
        # To handle concurrency we essentially "reserve" our spot in
        # the linecache with a dummy line.  The caller can then
        # set this value correctly.
        cache_line = (1, None, (str(unique_id),), unique_filename)
        if (
            linecache.cache.setdefault(unique_filename, cache_line)
            == cache_line
        ):
            return unique_filename

        # Looks like this spot is taken. Try again.
        count += 1
        extra = "-{0}".format(count)
