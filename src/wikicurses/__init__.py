from enum import IntEnum


class formats(IntEnum):
    i, b, blockquote = (1 << i for i in range(3))
