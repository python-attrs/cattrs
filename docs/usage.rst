=====================
Common Usage Examples
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

    @attr.s
    class MyRecord:
        a_string: str = attr.ib()
        a_datetime: DateTime = attr.ib()

Next, we register hooks for the ``DateTime`` class on a new :class:`.Converter` instance.

.. code-block:: python

    converter = Converter()

    converter.register_unstructure_hook(DateTime, lambda dt: dt.timestamp())

    converter.register_structure_hook(DateTime, lambda ts, _: pendulum.from_timestamp(ts))

And we can proceed with unstructuring and structuring instances of ``MyRecord``.

.. testsetup:: pendulum

    import pendulum
    from pendulum import DateTime

    @attr.s
    class MyRecord:
        a_string: str = attr.ib()
        a_datetime: DateTime = attr.ib()

    converter = cattr.Converter()
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


.. _Pendulum: https://pendulum.eustace.io/