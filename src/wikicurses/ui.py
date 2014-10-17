import urwid
from wikicurses import formats
from wikicurses.settings import Settings, conf
from wikicurses.wiki import Wiki

def tabComplete(text, matches):
    if not matches:
        return text
    matches = sorted(matches, key=len)
    if matches[0] == text and len(matches)>1:
        match = matches[1]
    else:
        match = matches[0]
    return match

class SearchBox(urwid.Edit):
    def keypress(self, size, key):
        if key == 'enter':
            loop.widget = mainwidget
            setContent(wiki.search(self.edit_text or 'Main page'))
        elif key == 'tab':
            matches = wiki.search_sugestions(self.edit_text)
            match = tabComplete(self.edit_text, matches)
            self.set_edit_text(match)
            self.edit_pos = len(match)
        else:
            return super().keypress(size, key)


class SelectorBox(urwid.ListBox):
    def __init__(self):
        def selectButton(radio_button, new_state, parameter):
            if new_state:
                loop.widget = mainwidget
                self._select(parameter)

        super().__init__(urwid.SimpleFocusListWalker([]))
        for i, (name, selected, parameter) in enumerate(self._items()):
            urwid.RadioButton(self.body, name, selected, selectButton, parameter)
            if selected:
                self.set_focus(i)

class Results(SelectorBox):
    def __init__(self, results):
        self.results = results
        super().__init__()

    def _items(self):
        return ((i, False, i) for i in self.results)

    def _select(self, title):
        setContent(wiki.search(title))

class Toc(SelectorBox):
    def _items(self):
        return ((name, widgets.focus>=ind, ind) for name, ind in widgetnames)
    
    def _select(self, index):
       widgets.set_focus(index)

class Bmarks(SelectorBox):
    def _items(self):
        self.deleted = []
        return ((i, False, i) for i in bmarks)

    def _select(self, name):
        setContent(wiki.search(name))

    def keypress(self, size, key):
        #Undo Delete
        if key == 'u' and self.deleted:
            index, item = self.deleted.pop()
            bmarks.add(item.label)
            self.body.insert(index, item)
            self.set_focus(index)
        elif key in ('meta [', 'x') and self.focus:
            bmarks.discard(self.focus.label)
            self.deleted.append((self.focus_position, self.focus))
            self.body.remove(self.focus)
        else:
            return super().keypress(size, key)

class Wikis(SelectorBox):
    def _items(self):
        wikis = (i for i in conf if i not in ('general', 'DEFAULT'))
        for name in wikis:
            yield name, wiki.siteurl == conf[name]['url'], name

    def _select(self, name):
        openWiki(name)
        setContent(wiki.search('Main page'))

class Ex(urwid.Edit):
    def keypress(self, size, key):
        if key == 'esc' or (key == 'backspace' and not self.edit_text):
            self.exitexmode()
        elif key == 'tab':
            cmds = ('quit', 'bmark', 'bmarks', 'wikis')
            matches = [i for i in cmds if i.startswith(self.edit_text)]
            match = tabComplete(self.edit_text, matches)
            self.set_edit_text(match)
            self.edit_pos = len(match)
        elif key == 'enter':
            cmd = self.edit_text
            self.exitexmode()
            self.processCmd(cmd)
        else:
            return super().keypress(size, key)

    def processCmd(self, cmd):
        if cmd in ('q', 'quit'):
            raise urwid.ExitMainLoop
        if cmd == 'bmarks':
            openOverlay(Bmarks(), "Bookmarks")
        elif cmd == 'bmark':
            bmarks.add(header.text)
            notify("Bookmark Added")
        elif cmd == 'wikis':
            openOverlay(Wikis(), "Wikis")
        elif cmd:
            notify(cmd + ': Unknown Command')

    def exitexmode(self):
        self.set_caption('')
        self.set_edit_text('')
        mainwidget.set_focus('body')

    def enterexmode(self):
        mainwidget.set_focus('footer')
        self.set_caption(':')

def notify(text):
    mainwidget.footer = urwid.Text(text)

def openOverlay(widget, title, height=('relative', 50), width=('relative', 50)):
    box = urwid.LineBox(widget, title)
    overlay = urwid.Overlay(box, mainwidget, 'center', width, 'middle', height)
    loop.widget = overlay

def keymapper(input):
    #TODO: Implement gg and G

    if input == 'q':
        raise  urwid.ExitMainLoop
    elif input == ':':
        mainwidget.footer.enterexmode()
    elif input == 'c':
        openOverlay(Toc(), "Table of Contents")
    elif input == 'o':
        openOverlay(urwid.ListBox([SearchBox()]), "Search", height=3)
    elif input == 'esc':
        loop.widget = mainwidget
    else:
       return False
    return True

def input_filter(keys, raw):
    if not isinstance(mainwidget.footer, urwid.Edit):
        mainwidget.footer = Ex()
    return keys

def openWiki(name):
    global wiki
    global bmarks
    if not name:
        url = conf[conf['general']['default']]['url']
    elif name in conf:
        url = conf[name]['url']
    else:
        url = name
    wiki = Wiki(url)
    bmarks = Settings(url, 'bookmarks')

def setContent(page):
    if not page.exists:
        results = wiki.search_sugestions(page.title)
        if results:
            openOverlay(Results(results), 'Results')
            return

    widgets.clear()
    widgetnames.clear()
    header.set_text(page.title)
    for title, content in page.content.items():
        if title:
            h2 = urwid.Text([('h2', title), '\n'], align="center")
            widgets.append(h2)
            widgetnames.append((title, widgets.index(h2)))
        else:
            widgetnames.append((page.title, 0))
        widgets.append(urwid.Text(content))


palette = [('h1', 'bold', 'dark blue'),
           ('h2', 'underline', ''),
           ('h', 'underline', '')]

#(ITALIC, 'italic') does not work. No italics option?
outputfmt = (('b', 'bold'), ('blockquote', 'dark gray'))
for x in range(1, sum(formats) + 1):
    fmt = ','.join(j for i, j in outputfmt if x&formats[i])
    palette.append((x, fmt, ''))

widgets = urwid.SimpleFocusListWalker([])
widgetnames = []
pager = urwid.ListBox(widgets)

header = urwid.Text('Wikicurses', align='center')
mainwidget = urwid.Frame(pager, urwid.AttrMap(header, 'h1'), Ex())

urwid.command_map['k'] = 'cursor up'
urwid.command_map['j'] = 'cursor down'
urwid.command_map['ctrl b'] = 'cursor page up'
urwid.command_map['ctrl f'] = 'cursor page down'


loop = urwid.MainLoop(mainwidget, palette=palette, handle_mouse=False,
                     unhandled_input=keymapper, input_filter=input_filter)
