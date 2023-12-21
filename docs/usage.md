# Advanced Examples

This section covers advanced use examples of _cattrs_ features.

## Using Factory Hooks

For this example, let's assume you have some attrs classes with snake case attributes, and you want to un/structure them as camel case.

```{warning}
A simpler and better approach to this problem is to simply make your class attributes camel case.
However, this is a good example of the power of hook factories and _cattrs'_ composition-based design.
```

Here's our simple data model:

```python
@define
class Inner:
    a_snake_case_int: int
    a_snake_case_float: float
    a_snake_case_str: str

@define
class Outer:
    a_snake_case_inner: Inner
```

Let's examine our options one by one, starting with the simplest: writing manual un/structuring hooks.

We just write the code by hand and register it:

```python
def unstructure_inner(inner):
    return {
        "aSnakeCaseInt": inner.a_snake_case_int,
        "aSnakeCaseFloat": inner.a_snake_case_float,
        "aSnakeCaseStr": inner.a_snake_case_str
    }

>>> converter.register_unstructure_hook(Inner, unstructure_inner)
```

(Let's skip the other unstructure hook and 2 structure hooks due to verbosity.)

This will get us where we want to go, but the drawbacks are immediately obvious:
we'd need to write a ton of code ourselves, wasting effort, increasing our
maintenance burden and risking bugs. Obviously this won't do.

Why write code when we can write code to write code for us? In this case this
code has already been written for you. _cattrs_ contains a module,
{mod}`cattrs.gen`, with functions to automatically generate hooks exactly like this.
These functions also take parameters to customize the generated hooks.

We can generate and register the renaming hooks we need:

```python
>>> from cattrs.gen import make_dict_unstructure_fn, override

>>> converter.register_unstructure_hook(
...     Inner,
...      make_dict_unstructure_fn(
...          Inner,
...          converter,
...          a_snake_case_int=override(rename="aSnakeCaseInt"),
...          a_snake_case_float=override(rename="aSnakeCaseFloat"),
...          a_snake_case_str=override(rename="aSnakeCaseStr"),
...      )
...  )
```

(Again skipping the other hooks due to verbosity.)

This is still too verbose and manual for our tastes, so let's automate it
further. We need a way to convert snake case identifiers to camel case, so
let's grab one from Stack Overflow:

```python
def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])
```

We can combine this with [`attrs.fields`](https://www.attrs.org/en/stable/api.html#attrs.fields) to save us some typing:

```python
from attrs import fields
from cattrs.gen import make_dict_unstructure_fn, override

converter.register_unstructure_hook(
    Inner,
    make_dict_unstructure_fn(
        Inner,
        converter,
        **{a.name: override(rename=to_camel_case(a.name)) for a in fields(Inner)}
    )
)

converter.register_unstructure_hook(
    Outer,
    make_dict_unstructure_fn(
        Outer,
        converter,
        **{a.name: override(rename=to_camel_case(a.name)) for a in fields(Outer)}
    )
)
```

(Skipping the structuring hooks due to verbosity.)

Now we're getting somewhere, but we still need to do this for each class
separately. The final step is using hook factories instead of hooks directly.

Hook factories are functions that return hooks. They are also registered using
predicates instead of being attached to classes directly, like normal
un/structure hooks. Predicates are functions that given a type return a
boolean whether they handle it.

We want our hook factories to trigger for all _attrs_ classes, so we need a
predicate to recognize whether a type is an _attrs_ class. Luckily, _attrs_ comes
with [`attrs.has`](https://www.attrs.org/en/stable/api.html#attrs.has), which is exactly this.

As the final step, we can combine all of this into two hook factories:

```python
from attrs import has, fields
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn, make_dict_structure_fn, override

converter = Converter()

def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

def to_camel_case_unstructure(cls):
    return make_dict_unstructure_fn(
        cls,
        converter,
        **{
            a.name: override(rename=to_camel_case(a.name))
            for a in fields(cls)
        }
    )

def to_camel_case_structure(cls):
    return make_dict_structure_fn(
        cls,
        converter,
        **{
            a.name: override(rename=to_camel_case(a.name))
            for a in fields(cls)
        }
    )

converter.register_unstructure_hook_factory(
    has, to_camel_case_unstructure
)
converter.register_structure_hook_factory(
    has, to_camel_case_structure
)
```

The `converter` instance will now un/structure every attrs class to camel case.
Nothing has been omitted from this final example; it's complete.


## Using Fallback Key Names

Sometimes when structuring data, the input data may be in multiple formats that need to be converted into a common attribute.

Consider an example where a data store creates a new schema version and renames a key (ie, `{'old_field':  'value1'}` in v1 becomes `{'new_field': 'value1'}` in v2), while also leaving existing records in the system with the V1 schema. Both keys should convert to the same field.

Here, builtin customizations such as [rename](./customizing.md#rename) are insufficient - _cattrs_ cannot structure both `old_field` and `new_field` into a single field using `rename`, at least not on the same converter.

In order to support both fields, you can apply a little preprocessing to the default _cattrs_ structuring hooks.
One approach is to write the following decorator and apply it to your class.

```python
from attrs import define
from cattrs import Converter
from cattrs.gen import make_dict_structure_fn

converter = Converter()


def fallback_field(
    converter_arg: Converter,
    old_to_new_field: dict[str, str]
):
    def decorator(cls):
        struct = make_dict_structure_fn(cls, converter_arg)

        def structure(d, cl):
            for k, v in old_to_new_field.items():
                if k in d:
                    d[v] = d[k]

            return struct(d, cl)

        converter_arg.register_structure_hook(cls, structure)

        return cls

    return decorator


@fallback_field(converter, {"old_field": "new_field"})
@define
class MyInternalAttr:
    new_field: str
```

_cattrs_ will now structure both key names into `new_field` on your class.

```python
converter.structure({"new_field": "foo"}, MyInternalAttr)
converter.structure({"old_field": "foo"}, MyInternalAttr)
```
