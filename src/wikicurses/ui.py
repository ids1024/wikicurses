from collections import OrderedDict
import urwid
from wikicurses import formats
#TODO: Turn this into a class?

screen = urwid.raw_display.Screen() 
screen.register_palette_entry('h1', 'bold', '')
screen.register_palette_entry('h2', 'underline', '')
screen.register_palette_entry('h', 'underline', '')

#(ITALIC, 'italic') does not work. No italics option?
outputfmt = (('b', 'bold'), ('blockquote', 'dark gray'))
for x in range(1, sum(formats) + 1):
    fmt = ','.join(j for i, j in outputfmt if x&formats[i])
    screen.register_palette_entry(x, fmt, '')

widgets = urwid.listbox.SimpleFocusListWalker([])
widgetnames = OrderedDict()

pager = urwid.ListBox(widgets)
pager._command_map['k'] = 'cursor up'
pager._command_map['j'] = 'cursor down'
pager._command_map['ctrl b'] = 'cursor page up'
pager._command_map['ctrl f'] = 'cursor page down'

def selectWidget(radio_button, new_state, args):
    if new_state:
        widget = args[0]
        index = widgets.index(widget)
        loop.widget = pager
        widgets.set_focus(index)

def keymapper(input):
    #TODO: Implement gg and G
    if input == 'q':
        raise  urwid.ExitMainLoop
    elif input == 'c':
        if loop.widget is pager:
            for widget in widgetnames.values():
                if widgets.focus >= widgets.index(widget):
                    current = widget
                else:
                    break
            radiobuttons = []
            for name, widget in widgetnames.items():
                urwid.RadioButton(radiobuttons, name, state=(current==widget),
                        on_state_change=selectWidget, user_data=[widget])
            toc = urwid.LineBox(urwid.ListBox(radiobuttons))
            overlay = urwid.Overlay(toc, pager,
                'center', ('relative', 50), 'middle', ('relative', 50))
            loop.widget = overlay
        else:
            loop.widget = pager
    else:
       return False
    return True

loop = urwid.MainLoop(pager, screen=screen, handle_mouse=False,
                     unhandled_input=keymapper)

def setContent(title, content):
    widgets.clear()
    widgetnames.clear()
    h1 = urwid.Text([('h1', title), '\n'], align="center")
    widgets.append(h1)
    widgetnames[title] = h1
    for title, content in content.items():
        if title:
            h2 = urwid.Text([('h1', title), '\n'], align="center")
            widgets.append(h2)
            widgetnames[title] = h2
        widgets.append(urwid.Text(content))
