==========
Validation
==========

`cattrs` has a detailed validation mode since version 22.1.0, and this mode is enabled by default.
When running under detailed validation, the un/structuring hooks are slightly slower but produce more precise and exhaustive error messages.

Detailed validation
-------------------
In detailed validation mode, any un/structuring errors will be grouped and raised together as a ``cattrs.BaseValidationError``, which is a `PEP 654 ExceptionGroup`_.
ExceptionGroups are special exceptions which contain lists of other exceptions, which may themselves be other ExceptionGroups.
In essence, ExceptionGroups are trees of exceptions.

When un/structuring a class, `cattrs` will gather any exceptions on a field-by-field basis and raise them as a ``cattrs.ClassValidationError``, which is a subclass of ``BaseValidationError``.
When structuring sequences and mappings, `cattrs` will gather any exceptions on a key- or index-basis and raise them as a ``cattrs.IterableValidationError``, which is a subclass of ``BaseValidationError``.

The exceptions will also have their ``__notes__`` attributes set, as per `PEP 678`_, showing the field, key or index for each inner exception.

A simple example involving a class containing a list and a dictionary:

.. code-block:: python

    @define
    class Class:
        a_list: list[int]
        a_dict: dict[str, int]

    >>> structure({"a_list": ["a"], "a_dict": {"str": "a"}})
      + Exception Group Traceback (most recent call last):
      |   File "<stdin>", line 1, in <module>
      |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 276, in structure
      |     return self._structure_func.dispatch(cl)(obj, cl)
      |   File "<cattrs generated structure __main__.Class>", line 14, in structure_Class
      |     if errors: raise __c_cve('While structuring Class', errors, __cl)
      | cattrs.errors.ClassValidationError: While structuring Class
      +-+---------------- 1 ----------------
        | Exception Group Traceback (most recent call last):
        |   File "<cattrs generated structure __main__.Class>", line 5, in structure_Class
        |     res['a_list'] = __c_structure_a_list(o['a_list'], __c_type_a_list)
        |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 457, in _structure_list
        |     raise IterableValidationError(
        | cattrs.errors.IterableValidationError: While structuring list[int]
        | Structuring class Class @ attribute a_list
        +-+---------------- 1 ----------------
          | Traceback (most recent call last):
          |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 450, in _structure_list
          |     res.append(handler(e, elem_type))
          |   File "/Users/tintvrtkovic/pg/cattrs/src/cattr/converters.py", line 375, in _structure_call
          |     return cl(obj)
          | ValueError: invalid literal for int() with base 10: 'a'
          | Structuring list[int] @ index 0
          +------------------------------------
        +---------------- 2 ----------------
        | Exception Group Traceback (most recent call last):
        |   File "<cattrs generated structure __main__.Class>", line 10, in structure_Class
        |     res['a_dict'] = __c_structure_a_dict(o['a_dict'], __c_type_a_dict)
        |   File "", line 17, in structure_mapping
        | cattrs.errors.IterableValidationError: While structuring dict
        | Structuring class Class @ attribute a_dict
        +-+---------------- 1 ----------------
          | Traceback (most recent call last):
          |   File "", line 5, in structure_mapping
          | ValueError: invalid literal for int() with base 10: 'a'
          | Structuring mapping value @ key 'str'
          +------------------------------------

.. _`PEP 654 ExceptionGroup`: https://www.python.org/dev/peps/pep-0654/
.. _`PEP 678`: https://www.python.org/dev/peps/pep-0678/

Non-detailed validation
-----------------------

Non-detailed validation can be enabled by initializing any of the converters with ``detailed_validation=False``.
In this mode, any errors during un/structuring will bubble up directly as soon as they happen.
