# Why *cattrs*?

Python has a rich set of powerful, easy to use, built-in **unstructured** data types like dictionaries, lists and tuples.
These data types effortlessly convert into common serialization formats like JSON, MessagePack, CBOR, YAML or TOML.

But the data that is used by your **business logic** should be **structured** into well-defined classes, since not all combinations of field names or values are valid inputs to your programs.
The more trust you can have into the structure of your data, the simpler your code can be, and the fewer edge cases you have to worry about.

When you're handed unstructured data (by your network, file system, database, ...), _cattrs_ helps to convert this data into trustworthy structured data.
When you have to convert your structured data into data types that other libraries can handle, _cattrs_ turns your classes and enumerations into dictionaries, integers and strings.

_attrs_ (and to a certain degree dataclasses) are excellent libraries for declaratively describing the structure of your data, but they're purposefully not serialization libraries.
*cattrs* is there for you the moment your `attrs.asdict(your_instance)` and `YourClass(**data)` start failing you because you need more control over the conversion process.


## Examples

```{include} ../README.md
:start-after: "begin-example -->"
:end-before: "<!-- end-example"
```

:::{important}
Note how the structuring and unstructuring details do **not** pollute your class, meaning: your data model.
Any needs to configure the conversion are done within *cattrs* itself, not within your data model.

There are popular validation libraries for Python that couple your data model with its validation and serialization rules based on, for example, web APIs.
We think that's the wrong approach.
Validation and serializations are concerns of the edges of your program – not the core.
They should neither apply design pressure on your business code, nor affect the performance of your code through unnecessary validation.
In bigger real-world code bases it's also common for data coming from multiple sources that need different validation and serialization rules.

🎶 You gotta keep 'em separated. 🎶
:::


*cattrs* also works with the usual Python collection types like dictionaries, lists, or tuples when you want to **normalize** unstructured data data into a certain (still unstructured) shape.
For example, to convert a list of a float, an int and a string into a tuple of ints:

```python
>>> import cattrs

>>> cattrs.structure([1.0, 2, "3"], tuple[int, int, int])
(1, 2, 3)

```

Finally, here's a much more complex example, involving _attrs_ classes where _cattrs_ interprets the type annotations to structure and unstructure the data correctly, including Enums and nested data structures:

```python
>>> from enum import unique, Enum
>>> from typing import Sequence
>>> from cattrs import structure, unstructure
>>> from attrs import define, field

>>> @unique
... class CatBreed(Enum):
...     SIAMESE = "siamese"
...     MAINE_COON = "maine_coon"
...     SACRED_BIRMAN = "birman"

>>> @define
... class Cat:
...     breed: CatBreed
...     names: Sequence[str]

>>> @define
... class DogMicrochip:
...     chip_id = field()  # Type annotations are optional, but recommended
...     time_chipped: float = field()

>>> @define
... class Dog:
...     cuteness: int
...     chip: DogMicrochip | None = None

>>> p = unstructure([Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)),
...                  Cat(breed=CatBreed.MAINE_COON, names=('Fluffly', 'Fluffer'))])

>>> p
[{'cuteness': 1, 'chip': {'chip_id': 1, 'time_chipped': 10.0}}, {'breed': 'maine_coon', 'names': ['Fluffly', 'Fluffer']}]
>>> structure(p, list[Dog | Cat])
[Dog(cuteness=1, chip=DogMicrochip(chip_id=1, time_chipped=10.0)), Cat(breed=<CatBreed.MAINE_COON: 'maine_coon'>, names=['Fluffly', 'Fluffer'])]

```

:::{tip}
Consider unstructured data a low-level representation that needs to be converted to structured data to be handled, and use `structure()`.
When you're done, `unstructure()` the data to its unstructured form and pass it along to another library or module.
:::


```{include} ../README.md
:start-after: "begin-why -->"
:end-before: "<!-- end-why"
```


## Additional Documentation and Talks

- [On structured and unstructured data, or the case for cattrs](https://threeofwands.com/on-structured-and-unstructured-data-or-the-case-for-cattrs/)
- [Why I use attrs instead of pydantic](https://threeofwands.com/why-i-use-attrs-instead-of-pydantic/)
- [cattrs I: un/structuring speed](https://threeofwands.com/why-cattrs-is-so-fast/)
- [Python has a macro language - it's Python (PyCon IT 2022)](https://www.youtube.com/watch?v=UYRSixikUTo)
- [Intro to cattrs 23.1](https://threeofwands.com/intro-to-cattrs-23-1-0/)
