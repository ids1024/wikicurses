import pkgutil
from enum import Enum

_data = pkgutil.get_data('wikicurses', 'interwiki.list').decode()
wikis = dict([i.split('|')[0:2] for i in _data.splitlines() if i[0]!='#'])

class BitEnum(int, Enum):
    def __new__(cls, *args):
        value = 1 << len(cls.__members__)
        return int.__new__(cls, value)

formats = BitEnum("formats", "i b blockquote")
