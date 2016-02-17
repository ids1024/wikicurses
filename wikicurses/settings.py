import os
import json
import collections
import configparser
from wikicurses import formats
from urllib.parse import urlparse

default_configdir = os.environ['HOME'] + '/.config'
configpath = os.environ.get(
    'XDG_CONFIG_HOME', default_configdir) + '/wikicurses'

conf = configparser.ConfigParser()
conf.read(['/etc/wikicurses.conf', configpath + '/config'])

try:
    mouse = conf.getboolean('general', 'mouse')
except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
    mouse = False
try:
    hide_references = conf.getboolean('general', 'hide_references')
except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
    hide_references = False

Attribute = collections.namedtuple('Attribute',
        ('settings', 'fgcolor', 'bgcolor', 'align', 'padding', 'border'))
defcolors = {
        'b': Attribute(['bold',], '', '', '', 0, False),
        'blockquote': Attribute([], 'dark gray', '', '', 0, False),
        'searchresult': Attribute(['standout'], '', '', '', 0, False),
        'h1': Attribute(['bold'], '', 'dark blue', '', 0, False),
        'h2': Attribute(['bold', 'underline'], 'dark blue', '', 'center', 0, False),
        'h': Attribute(['bold', 'underline'], 'dark blue', '', '', 0, False),
        'pre': Attribute([], 'dark green', '', '', 3, False),
        'code': Attribute([], '', '', '', 0, False),
        'divpadding': Attribute([], '', '', '', 6, False),
        'divborder': Attribute([], '', '', '', 0, True),
        }
colorspath = configpath + '/colors'
if os.path.exists(colorspath):
    colorsconf = configparser.ConfigParser()
    colors = {}
    colorsconf.read(colorspath)
    for name, defattr in defcolors.items():
        try:
            settings = colorsconf.get(name, 'settings').split()
        except (configparser.NoSectionError, configparser.NoOptionError):
            settings = defattr.settings
        fgcolor = colorsconf.get(name, 'fgcolor', fallback=defattr.fgcolor)
        bgcolor = colorsconf.get(name, 'bgcolor', fallback=defattr.bgcolor)
        align = colorsconf.get(name, 'align', fallback=defattr.align)
        padding = colorsconf.getint(name, 'padding', fallback=defattr.padding)
        border = colorsconf.getboolean(name, 'border', fallback=defattr.border)
        colors[name] = Attribute(settings,
                fgcolor, bgcolor, align, padding, border)
else:
    colors = defcolors

def getColor(tformat, name, default=''):
    values = [j for j in (getattr(colors[i.name], name) for i in formats
              if tformat & i and i.name in colors) if j]
    return values[-1] if values else default

def dumpColors():
    colorsconf = configparser.ConfigParser()
    for name, (settings, fgcolor, bgcolor, align, padding, border) in colors.items():
        colorsconf.add_section(name)
        colorsconf.set(name, 'settings', ' '.join(settings))
        colorsconf.set(name, 'fgcolor', fgcolor)
        colorsconf.set(name, 'bgcolor', bgcolor)
        colorsconf.set(name, 'align', align)
        colorsconf.set(name, 'padding', str(padding))
        colorsconf.set(name, 'border', str(border))
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
