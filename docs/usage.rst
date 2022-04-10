=====================
Common usage examples
=====================

This section covers common use examples of cattrs features.

Using Pendulum for Dates and Time
---------------------------------

To use the excellent Pendulum_ library for datetimes, we need to register
structuring and unstructuring hooks for it.

First, we need to decide on the unstructured representation of a datetime
instance. Since all our datetimes will use the UTC time zone, we decide to
use the UNIX epoch timestamp as our unstructured representation.

Define a class using Pendulum's DateTime:

.. code-block:: python

    import pendulum
    from pendulum import DateTime

    @define
    class MyRecord:
        a_string: str
        a_datetime: DateTime

Next, we register hooks for the ``DateTime`` class on a new :class:`.Converter` instance.

.. code-block:: python

    converter = Converter()

    converter.register_unstructure_hook(DateTime, lambda dt: dt.timestamp())

    converter.register_structure_hook(DateTime, lambda ts, _: pendulum.from_timestamp(ts))

And we can proceed with unstructuring and structuring instances of ``MyRecord``.

.. testsetup:: pendulum

    import pendulum
    from pendulum import DateTime

    @define
    class MyRecord:
        a_string: str
        a_datetime: DateTime

    converter = cattrs.Converter()
    converter.register_unstructure_hook(DateTime, lambda dt: dt.timestamp())
    converter.register_structure_hook(DateTime, lambda ts, _: pendulum.from_timestamp(ts))

.. doctest:: pendulum

    >>> my_record = MyRecord('test', pendulum.datetime(2018, 7, 28, 18, 24))
    >>> my_record
    MyRecord(a_string='test', a_datetime=DateTime(2018, 7, 28, 18, 24, 0, tzinfo=Timezone('UTC')))

    >>> converter.unstructure(my_record)
    {'a_string': 'test', 'a_datetime': 1532802240.0}

    >>> converter.structure({'a_string': 'test', 'a_datetime': 1532802240.0}, MyRecord)
    MyRecord(a_string='test', a_datetime=DateTime(2018, 7, 28, 18, 24, 0, tzinfo=Timezone('UTC')))


After a while, we realize we *will* need our datetimes to have timezone information.
We decide to switch to using the ISO 8601 format for our unstructured datetime instances.

.. testsetup:: pendulum-iso8601

    import pendulum
    from pendulum import DateTime

    @define
    class MyRecord:
        a_string: str
        a_datetime: DateTime

.. doctest:: pendulum-iso8601

    >>> converter = cattrs.Converter()
    >>> converter.register_unstructure_hook(DateTime, lambda dt: dt.to_iso8601_string())
    >>> converter.register_structure_hook(DateTime, lambda isostring, _: pendulum.parse(isostring))

    >>> my_record = MyRecord('test', pendulum.datetime(2018, 7, 28, 18, 24, tz='Europe/Paris'))
    >>> my_record
    MyRecord(a_string='test', a_datetime=DateTime(2018, 7, 28, 18, 24, 0, tzinfo=Timezone('Europe/Paris')))

    >>> converter.unstructure(my_record)
    {'a_string': 'test', 'a_datetime': '2018-07-28T18:24:00+02:00'}

    >>> converter.structure({'a_string': 'test', 'a_datetime': '2018-07-28T18:24:00+02:00'}, MyRecord)
    MyRecord(a_string='test', a_datetime=DateTime(2018, 7, 28, 18, 24, 0, tzinfo=Timezone('+02:00')))

Using factory hooks
-------------------

For this example, let's assume you have some attrs classes with snake case attributes, and you want to
un/structure them as camel case.

.. warning:: A simpler and better approach to this problem is to simply make your class attributes camel case.
   However, this is a good example of the power of hook factories and cattrs' component-based design.

Here's our simple data model:

.. code-block:: python

    @define
    class Inner:
        a_snake_case_int: int
        a_snake_case_float: float
        a_snake_case_str: str

    @define
    class Outer:
        a_snake_case_inner: Inner

Let's examine our options one by one, starting with the simplest: writing manual un/structuring hooks.

We just write the code by hand and register it:

.. code-block:: python

    def unstructure_inner(inner):
        return {
            "aSnakeCaseInt": inner.a_snake_case_int,
            "aSnakeCaseFloat": inner.a_snake_case_float,
            "aSnakeCaseStr": inner.a_snake_case_str
        }

    converter.register_unstructure_hook(Inner, unstructure_inner)

(Let's skip the other unstructure hook and 2 structure hooks due to verbosity.)

This will get us where we want to go, but the drawbacks are immediately obvious:
we'd need to write a ton of code ourselves, wasting effort, increasing our
maintenance burden and risking bugs. Obviously this won't do.

Why write code when we can write code to write code for us? In this case this
code has already been written for you. cattrs contains a module,
:py:mod:`cattrs.gen`, with functions to automatically generate hooks exactly like this.
These functions also take parameters to customize the generated hooks.

We can generate and register the renaming hooks we need:

.. code-block:: python

    from cattrs.gen import make_dict_unstructure_fn, override

    converter.register_unstructure_hook(
        Inner,
        make_dict_unstructure_fn(
            Inner,
            converter,
            a_snake_case_int=override(rename="aSnakeCaseInt"),
            a_snake_case_float=override(rename="aSnakeCaseFloat"),
            a_snake_case_str=override(rename="aSnakeCaseStr"),
        )
    )

(Again skipping the other hooks due to verbosity.)

This is still too verbose and manual for our tastes, so let's automate it
further. We need a way to convert snake case identifiers to camel case, so
let's grab one from Stack Overflow:

.. code-block:: python

    def to_camel_case(snake_str: str) -> str:
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

We can combine this with ``attr.fields`` to save us some typing:

.. code-block:: python

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

(Skipping the structuring hooks due to verbosity.)

Now we're getting somewhere, but we still need to do this for each class
separately. The final step is using hook factories instead of hooks directly.

Hook factories are functions that return hooks. They are also registered using
predicates instead of being attached to classes directly, like normal
un/structure hooks. Predicates are functions that given a type return a
boolean whether they handle it.

We want our hook factories to trigger for all attrs classes, so we need a
predicate to recognize whether a type is an attrs class. Luckily, attrs comes
with ``attr.has``, which is exactly this.

As the final step, we can combine all of this into two hook factories:

.. code-block:: python

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

The ``converter`` instance will now un/structure every attrs class to camel case.
Nothing has been omitted from this final example; it's complete.

.. _Pendulum: https://pendulum.eustace.io/
