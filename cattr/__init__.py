# -*- coding: utf-8 -*-
from .converters import Converter

__author__ = 'Tin Tvrtković'
__email__ = 'tinchester@gmail.com'


global_converter = Converter()

unstructure = global_converter.unstructure
structure = global_converter.structure
structure_attrs_fromtuple = global_converter.structure_attrs_fromtuple
structure_attrs_fromdict = global_converter.structure_attrs_fromdict
