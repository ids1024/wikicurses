import os
import json
from urllib.parse import urlparse
from configparser import ConfigParser
from enum import Enum
from wikicurses.wiki import Wiki

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

def openWiki(name):
    global wiki
    global bmarks
    if not name:
        name = conf['general']['default']
    if name in conf:
        url = conf[name]['url']
        username = conf[name].get('username')
        password = conf[name].get('password')
    else:
        url = name
        username = password = ''
    wiki = Wiki(url, username, password)
    bmarks = Settings(url, 'bookmarks')

def wikis():
    exclude = ('general', 'DEFAULT', 'keymap')
    return {k: v['url'] for k, v in conf.items() if k not in exclude}
