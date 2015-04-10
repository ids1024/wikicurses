import os
import json
from urllib.parse import urlparse
import configparser

default_configdir = os.environ['HOME'] + '/.config'
configpath = os.environ.get(
    'XDG_CONFIG_HOME', default_configdir) + '/wikicurses'

conf = configparser.ConfigParser()
conf.read(['/etc/wikicurses.conf', configpath + '/config'])

try:
    mouse = conf.getboolean('general', 'mouse')
except (ValueError, configparser.NoOptionError):
    mouse = False
try:
    hide_references = conf.getboolean('general', 'hide_references')
except (ValueError, configparser.NoOptionError):
    hide_references = False

defcolors = {
        'b': [['bold',], '', ''],
        'blockquote': [[], 'dark gray', ''],
        'searchresult': [['standout'], '', ''],
        'h1': [['bold'], '', 'dark blue'],
        'h2': [['bold', 'underline'], '', ''],
        'h': [['bold', 'underline'], '', '']
        }
colorspath = configpath + '/colors'
if os.path.exists(colorspath):
    colorsconf = configparser.ConfigParser()
    colors = {}
    colorsconf.read(colorspath)
    for name, (defsettings, deffgcolor, defbgcolor) in defcolors.items():
        try:
            settings = colorsconf.get(name, 'settings').split()
        except (configparser.NoSectionError, configparser.NoOptionError):
            settings = defsettings
        fgcolor = colorsconf.get(name, 'fgcolor', fallback=deffgcolor)
        bgcolor = colorsconf.get(name, 'bgcolor', fallback=defbgcolor)
        colors[name] = [settings, fgcolor, bgcolor]
else:
    colors = defcolors

def dumpColors():
    colorsconf = configparser.ConfigParser()
    for name, (settings, fgcolor, bgcolor) in colors.items():
        colorsconf.add_section(name)
        colorsconf.set(name, 'settings', ' '.join(settings))
        colorsconf.set(name, 'fgcolor', fgcolor)
        colorsconf.set(name, 'bgcolor', bgcolor)
    with open(colorspath, 'w') as file:
        colorsconf.write(file)

class Settings:

    def __init__(self, wiki, name):
        self.configpath = configpath + '/' + urlparse(wiki).netloc
        self.file = self.configpath + '/' + name

    def __iter__(self):
        if not os.path.exists(self.file):
            return iter(())
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


def wikis():
    """Return dictionary of wiki urls by name."""
    exclude = ('general', 'DEFAULT', 'keymap')
    return {k: v['url'] for k, v in conf.items() if k not in exclude}
