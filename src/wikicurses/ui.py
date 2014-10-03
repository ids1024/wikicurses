from collections import OrderedDict
import urwid
from wikicurses import formats
#TODO: Turn this into a class?

screen = urwid.raw_display.Screen() 
screen.register_palette_entry('h1', 'bold', 'dark blue')
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

header = urwid.Text('Wikicurses', align='center')
mainwidget = urwid.Frame(pager, urwid.AttrMap(header, 'h1'))

pager._command_map['k'] = 'cursor up'
pager._command_map['j'] = 'cursor down'
pager._command_map['ctrl b'] = 'cursor page up'
pager._command_map['ctrl f'] = 'cursor page down'

def selectWidget(radio_button, new_state, args):
    if new_state:
        widget = args[0]
        index = widgets.index(widget)
        loop.widget = mainwidget
        widgets.set_focus(index)

def keymapper(input):
    #TODO: Implement gg and G
    if input == 'q':
        raise  urwid.ExitMainLoop
    elif input == 'c':
        if loop.widget is mainwidget:
            current = next(reversed([widget for widget in widgetnames.values()
                if widgets.focus >= widgets.index(widget)]), None)
            radiobuttons = []
            #Go to first widget when title is selected
            urwid.RadioButton(radiobuttons, header.text, state=(not current),
                    on_state_change=selectWidget, user_data=[widgets[0]])

            curbutton = 0
            for name, widget in widgetnames.items():
                button = urwid.RadioButton(radiobuttons, name, state=(current==widget),
                        on_state_change=selectWidget, user_data=[widget])
                if current == widget:
                    curbutton = radiobuttons.index(button)
            buttonbox = urwid.ListBox(radiobuttons)
            buttonbox.set_focus(curbutton)
            toc = urwid.LineBox(buttonbox, "Table of Contents")
            overlay = urwid.Overlay(toc, mainwidget,
                'center', ('relative', 50), 'middle', ('relative', 50))
            loop.widget = overlay
        else:
            loop.widget = mainwidget
    else:
       return False
    return True

loop = urwid.MainLoop(mainwidget, screen=screen, handle_mouse=False,
                     unhandled_input=keymapper)

def setContent(title, content):
    widgets.clear()
    widgetnames.clear()
    header.set_text(title)
    for title, content in content.items():
        if title:
            h2 = urwid.Text([('h2', title), '\n'], align="center")
            widgets.append(h2)
            widgetnames[title] = h2
        widgets.append(urwid.Text(content))
