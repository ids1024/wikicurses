import os
import json
import pkgutil
from enum import Enum

_data = pkgutil.get_data('wikicurses', 'interwiki.list').decode()
wikis = dict([i.split('|')[0:2] for i in _data.splitlines() if i[0]!='#'])

default_configdir = os.environ['HOME'] + '/.config'
configpath = os.environ.get('XDG_CONFIG_HOME', default_configdir) + '/wikicurses'

class Settings:
    def __init__(self, name):
        self.file = configpath + '/' + name

    def __iter__(self):
        if not os.path.exists(self.file):
            yield from ()
            return
        with open(self.file) as file:
            yield from json.load(file)

    def _save(self, bookmarks):
        if not os.path.exists(configpath):
            os.mkdir(configpath)
        with open(self.file, 'w') as file:
            json.dump(bookmarks, file)

    def add(self, bmark):
        bookmarks = set(self)
        bookmarks.add(bmark)
        self._save(list(bookmarks))

    def discard(self, bmark):
        bookmarks = set(self)
        bookmarks.discard(bmark)
        self._save(list(bookmarks))

bmarks = Settings('bookmarks')

class BitEnum(int, Enum):
    def __new__(cls, *args):
        value = 1 << len(cls.__members__)
        return int.__new__(cls, value)

formats = BitEnum("formats", "i b blockquote")
