from .converters import Converter

__author__ = 'Tin Tvrtković'
__email__ = 'tinchester@gmail.com'
__version__ = '0.2.0'


_global_converter = Converter()

dumps = _global_converter.dumps
loads = _global_converter.loads
