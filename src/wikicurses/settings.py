import os
import json
from urllib.parse import urlparse
from configparser import ConfigParser
from enum import Enum

default_configdir = os.environ['HOME'] + '/.config'
configpath = os.environ.get('XDG_CONFIG_HOME', default_configdir) + '/wikicurses'

conf = ConfigParser()
conf.read(['/etc/wikicurses.conf', configpath + '/config'])

class Settings:
    def __init__(self, wiki, name):
        self.configpath = configpath + '/' + urlparse(wiki).netloc
        self.file = self.configpath + '/' + name

    def __iter__(self):
        if not os.path.exists(self.file):
            yield from ()
            return
        with open(self.file) as file:
            yield from json.load(file)

    def _save(self, bookmarks):
        if not os.path.exists(self.configpath):
            os.makedirs(self.configpath)
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