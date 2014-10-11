import urwid
from wikicurses import formats, add_bookmark, remove_bookmark, get_bookmarks
from wikicurses.wiki import wiki
#TODO: Turn this into a class?


class SearchBox(urwid.Edit):
    def keypress(self, size, key):
        if key != 'enter':
            return super().keypress(size, key)
        loop.widget = mainwidget
        if self.edit_text:
            setContent(wiki.search(self.edit_text))
        else:
            setContent(wiki.get_featured_feed('featured'))

class Toc(urwid.ListBox):
    def __init__(self):
        def selectWidget(radio_button, new_state, index):
            if new_state:
                loop.widget = mainwidget
                widgets.set_focus(index)

        super().__init__(urwid.SimpleFocusListWalker([]))
        for i, (name, index) in enumerate(widgetnames):
            current = widgets.focus>=index
            urwid.RadioButton(self.body, name, current, selectWidget, index)
            if current:
                self.set_focus(i)

class Bmarks(urwid.ListBox):
    def __init__(self):
        def selectWidget(radio_button, new_state, bookmark):
            if new_state:
                loop.widget = mainwidget
                setContent(wiki.search(bookmark))

        super().__init__(urwid.SimpleFocusListWalker([]))
        for bookmark in get_bookmarks():
            urwid.RadioButton(self.body, bookmark, False, selectWidget, bookmark)
        self.deleted = []

    def keypress(self, size, key):
        if key == 'u': #Undo delete
            if not self.deleted:
                return
            index, item = self.deleted.pop()
            add_bookmark(item.label)
            self.body.insert(index, item)
            self.set_focus(index)
        if key in ('meta [', 'x'): #meta [ = delete
            if self.focus: #If there are any bookmarks
                remove_bookmark(self.focus.label)
                self.deleted.append((self.focus_position, self.focus))
                self.body.remove(self.focus)
        else:
            return super().keypress(size, key)

class Ex(urwid.Edit):
    def keypress(self, size, key):
        if key == 'esc' or (key == 'backspace' and not self.edit_text):
            self.exitexmode()
            return
        elif key != 'enter':
            return super().keypress(size, key)
        cmd = self.edit_text
        self.exitexmode()

        if cmd in ('q', 'quit'):
            raise urwid.ExitMainLoop
        if cmd == 'bmarks':
            openOverlay(Bmarks(), "Bookmarks")
        elif cmd == 'bmark':
            add_bookmark(header.text)
            notify("Bookmark Added")
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

def setContent(page):
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
