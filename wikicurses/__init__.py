from enum import IntEnum

__version__ = "1.4"

class formats(IntEnum):
    i, b, blockquote, searchresult, h1, h2, h, pre, code, \
            divpadding, divborder = (1 << i for i in range(11))
