from PIL import ImageFilter
from . import settings
from .exceptions import UnknownFilterException


filter_dict = {
    'EDGE_ENHANCE': ImageFilter.EDGE_ENHANCE,
    'EDGE_ENHANCE_MORE': ImageFilter.EDGE_ENHANCE_MORE,
    'SMOOTH': ImageFilter.SMOOTH,
    'SMOOTH_MORE': ImageFilter.SMOOTH_MORE,
    'SHARPEN': ImageFilter.SHARPEN
}


def get_filter(k):
    try:
        return filter_dict[k]()
    except KeyError:
        raise UnknownFilterException()


FILTERS = [get_filter(key) for key in settings.FILTERS]
