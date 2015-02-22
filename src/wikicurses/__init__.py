from enum import IntEnum


class formats(IntEnum):
    i, b, blockquote, searchresult = (1 << i for i in range(4))
