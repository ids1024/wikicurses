import os
import json
import pkgutil
from enum import Enum

_data = pkgutil.get_data('wikicurses', 'interwiki.list').decode()
wikis = dict([i.split('|')[0:2] for i in _data.splitlines() if i[0]!='#'])

default_configdir = os.environ['HOME'] + '/.config'
configpath = os.environ.get('XDG_CONFIG_HOME', default_configdir) + '/wikicurses'
bmarkfile = configpath + '/bookmarks'
def get_bookmarks():
    if not os.path.exists(bmarkfile):
        return []
    with open(bmarkfile) as file:
        return json.load(file)

def save_bookmarks(bmarks):
    if not os.path.exists(configpath):
        os.mkdir(configpath)
    with open(bmarkfile, 'w') as file:
        json.dump(bmarks, file)

def add_bookmark(title):
    bookmarks = set(get_bookmarks())
    bookmarks.add(title)
    save_bookmarks(list(bookmarks))

def remove_bookmark(title):
    bookmarks = set(get_bookmarks())
    bookmarks.discard(title)
    save_bookmarks(list(bookmarks))

class BitEnum(int, Enum):
    def __new__(cls, *args):
        value = 1 << len(cls.__members__)
        return int.__new__(cls, value)

formats = BitEnum("formats", "i b blockquote")
