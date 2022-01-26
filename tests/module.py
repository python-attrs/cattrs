from dataclasses import dataclass
from typing import List, Tuple

from attrs import define

from cattr import resolve_types


@dataclass
class DClass:
    ival: "IntType_1"
    ilist: List["IntType_2"]


@define
class AClass:
    ival: "IntType_3"
    ilist: List["IntType_4"]


@define
class ModuleClass:
    a: int


IntType_1 = int
IntType_2 = int
IntType_3 = int
IntType_4 = int

RecursiveTypeAliasM = List[Tuple[ModuleClass, "RecursiveTypeAliasM"]]
RecursiveTypeAliasM_1 = List[Tuple[ModuleClass, "RecursiveTypeAliasM_1"]]
RecursiveTypeAliasM_2 = List[Tuple[ModuleClass, "RecursiveTypeAliasM_2"]]

resolve_types(RecursiveTypeAliasM, globals(), locals())
resolve_types(RecursiveTypeAliasM_1, globals(), locals())
resolve_types(RecursiveTypeAliasM_2, globals(), locals())
