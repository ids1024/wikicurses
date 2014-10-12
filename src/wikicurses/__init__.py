from enum import Enum

class BitEnum(int, Enum):
    def __new__(cls, *args):
        value = 1 << len(cls.__members__)
        return int.__new__(cls, value)

formats = BitEnum("formats", "i b blockquote")
