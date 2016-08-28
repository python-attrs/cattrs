from .cattrs import Converter

__author__ = 'Tin Tvrtković'
__email__ = 'tinchester@gmail.com'
__version__ = '0.1.0'


_global_converter = Converter()

dumps = _global_converter.dumps
loads = _global_converter.loads
