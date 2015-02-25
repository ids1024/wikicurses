from enum import IntEnum


class formats(IntEnum):
    i, b, blockquote, searchresult, h1, h2, h = (1 << i for i in range(7))
