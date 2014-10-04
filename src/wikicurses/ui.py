import urwid
from wikicurses import formats
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
        super().__init__(urwid.SimpleFocusListWalker([]))

        current = next(j for i,j in reversed(widgetnames) if widgets.focus >= j)
        for name, widget in widgetnames:
            button = urwid.RadioButton(self.body, name, state=(current==widget))
            urwid.connect_signal(button, 'change', self._selectWidget, widget)
        #Focus selected button
        self.set_focus(next(x for x, i in enumerate(self.body) if i.state))

    def _selectWidget(self, radio_button, new_state, index):
        if new_state:
            loop.widget = mainwidget
            widgets.set_focus(index)

def openOverlay(widget, title, height=('relative', 50), width=('relative', 50)):
    box = urwid.LineBox(widget, title)
    overlay = urwid.Overlay(box, mainwidget, 'center', width, 'middle', height)
    loop.widget = overlay

def keymapper(input):
    #TODO: Implement gg and G
    if input == 'q':
        raise  urwid.ExitMainLoop
    elif input == 'c':
        openOverlay(Toc(), "Table of Contents")
    elif input == 'o':
        openOverlay(urwid.ListBox([SearchBox()]), "Search", height=3)
    elif input == 'esc':
        loop.widget = mainwidget
    else:
       return False
    return True

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


screen = urwid.raw_display.Screen() 
screen.register_palette_entry('h1', 'bold', 'dark blue')
screen.register_palette_entry('h2', 'underline', '')
screen.register_palette_entry('h', 'underline', '')

#(ITALIC, 'italic') does not work. No italics option?
outputfmt = (('b', 'bold'), ('blockquote', 'dark gray'))
for x in range(1, sum(formats) + 1):
    fmt = ','.join(j for i, j in outputfmt if x&formats[i])
    screen.register_palette_entry(x, fmt, '')

widgets = urwid.SimpleFocusListWalker([])
widgetnames = []
pager = urwid.ListBox(widgets)

header = urwid.Text('Wikicurses', align='center')
mainwidget = urwid.Frame(pager, urwid.AttrMap(header, 'h1'))

urwid.command_map['k'] = 'cursor up'
urwid.command_map['j'] = 'cursor down'
urwid.command_map['ctrl b'] = 'cursor page up'
urwid.command_map['ctrl f'] = 'cursor page down'


loop = urwid.MainLoop(mainwidget, screen=screen, handle_mouse=False,
                     unhandled_input=keymapper)
