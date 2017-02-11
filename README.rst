======
cattrs
======


.. image:: https://img.shields.io/pypi/v/cattrs.svg
        :target: https://pypi.python.org/pypi/cattrs

.. image:: https://img.shields.io/travis/Tinche/cattrs.svg
        :target: https://travis-ci.org/Tinche/cattrs

.. image:: https://readthedocs.org/projects/cattrs/badge/?version=latest
        :target: https://cattrs.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/Tinche/cattrs/shield.svg
        :target: https://pyup.io/repos/github/Tinche/cattrs/
        :alt: Updates

.. image:: https://codecov.io/gh/Tinche/cattrs/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/Tinche/cattrs

----

``cattrs`` is an experimental open source Python 3 library providing composable
complex class conversion support for ``attrs`` classes. Other kinds of classes
are supported by manually registering converters.

Python has a rich set of powerful, easy to use, built-in data types like
dictionaries, lists and tuples. These data types are also the lingua franca
of most data serialization libraries, for formats like json, msgpack, yaml or
toml.

Data types like this, and mappings like ``dict`` s in particular, represent
unstructured data. Your data is, in all likelihood, structured: not all
combinations of field names are values are valid inputs to your programs. In
Python, structured data is better represented with classes and enumerations.
``attrs`` is an excellent library for declaratively describing the structure of
your data, and validating it.

When you're handed unstructured data, ``cattrs`` helps to convert this data into
structured data. When you have to convert your structured data into data types
other libraries can handle, ``cattrs`` turns your classes and enumerations into
dictionaries, integers and strings.

A taste:

.. code-block:: python

    >>> from enum import unique, Enum
    >>> from typing import List, Sequence, Union
    >>> from cattr import loads, dumps
    >>> import attr
    >>> from attr.validators import instance_of, optional
    >>>
    >>> @unique
    ... class CatBreed(Enum):
    ...     SIAMESE = "siamese"
    ...     MAINE_COON = "maine_coon"
    ...     SACRED_BIRMAN = "birman"
    ...
    >>> @attr.s
    ... class Cat:
    ...     breed = attr.ib(validator=instance_of(CatBreed))
    ...     names = attr.ib(validator=instance_of(Sequence[str]))
    ...
    >>> @attr.s
    ... class DogMicrochip:
    ...     chip_id = attr.ib()
    ...     time_chipped = attr.ib(validator=instance_of(float))
    ...
    >>> @attr.s
    ... class Dog:
    ...     cuteness = attr.ib(validator=instance_of(int))
    ...     chip = attr.ib(validator=optional(instance_of(DogMicrochip)))
    ...
    >>> p = dumps([Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)),
    ...            Cat(breed=CatBreed.MAINE_COON, names=('Fluffly', 'Fluffer'))])
    ...
    >>> print(p)
    [{'chip': {'chip_id': 1, 'time_chipped': 10.0}, 'cuteness': 1}, {'names': ('Fluffly', 'Fluffer'), 'breed': 'maine_coon'}]
    >>> print(loads(p, List[Union[Dog, Cat]]))
    [Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)), Cat(breed=<CatBreed.MAINE_COON: 'maine_coon'>, names=['Fluffly', 'Fluffer'])]

``dumps`` and ``loads`` were chosen for their similarity to the functionality of
modules like ``marshal``, ``pickle`` and ``json``. Consider unstructured data a
low-level representation that needs to be converted to structured data to be
handled, and use ``loads``. When you're done, ``dumps`` the data to its
unstructured form and pass it along to another library or module.

* Free software: MIT license
* Documentation: https://cattrs.readthedocs.io.
* Python versions supported: 3.5 and up.


Features
--------

* Converts structured data into unstructured data, recursively:

  * ``attrs`` classes are converted into dictionaries, in a way similar to ``attrs.asdict``.
  * Enumeration instances are converted to their values.
  * Other types are let through without conversion. This includes types such as
    integers, dictionaries, lists and instances of non-``attrs`` classes.
  * Custom converters for any type can be registered using ``register_dumps_hook``.

* Converts unstructured data into structured data, recursively, according to
  your specification given as a type. The following types are supported:

  * ``typing.Optional[T]``.
  * ``typing.List[T]``, ``typing.MutableSequence[T]``, ``typing.Sequence[T]`` (converts to a list).
  * ``typing.Tuple`` (both variants, ``Tuple[T, ...]`` and ``Tuple[X, Y, Z]``).
  * ``typing.MutableSet[T]``, ``typing.Set[T]`` (converts to a set).
  * ``typing.FrozenSet[T]`` (converts to a frozenset).
  * ``typing.Dict[K, V]``, ``typing.MutableMapping[K, V]``, ``typing.Mapping[K, V]`` (converts to a dict).
  * ``attrs`` classes with simple attributes and the usual ``__init__``.

    * Simple attributes are attributes that can be assigned unstructured data,
      like numbers, strings, and collections of unstructured data.

  * All `attrs` classes with the usual ``__init__``, if their complex attributes
    have type metadata.
  * Custom converters for any type (including unions) can be registered using ``register_loads_hook``.

Credits
---------

Major credits to Hynek Schlawack for creating attrs_ and its predecessor,
characteristic_.

``cattrs`` is tested with Hypothesis_, by David R. MacIver.

``cattrs`` is benchmarked using perf_, by Victor Stinner.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _attrs: https://github.com/hynek/attrs
.. _characteristic: https://github.com/hynek/characteristic
.. _Hypothesis: http://hypothesis.readthedocs.io/en/latest/
.. _perf: https://github.com/haypo/perf
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

