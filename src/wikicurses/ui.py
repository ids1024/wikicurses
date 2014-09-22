import urwid
from wikicurses import ITALIC, BOLD, BLOCKQUOTE

screen = urwid.raw_display.Screen() 
screen.register_palette_entry('h1', 'yellow,bold', '')
screen.register_palette_entry('h2', 'underline', '')
screen.register_palette_entry('h', 'underline', '')

#(ITALIC, 'italic') does not work. No italics option?
outputfmt = ((BOLD, 'bold'), (BLOCKQUOTE, 'dark gray'))
for x in range(BOLD | ITALIC | BLOCKQUOTE + 1):
    fmt = ','.join(j for i, j in outputfmt if x&i)
    screen.register_palette_entry(BOLD, fmt, '')

def keymapper(input):
    #TODO: Implement gg and G
    if input == 'q':
        raise  urwid.ExitMainLoop
    else:
       return False
    return True

def createWindow(title, content):
    widgets = [urwid.Text([('h1', title), '\n'], align="center")]
    for title, content in content.items():
        if title:
            widgets.append(urwid.Text(['\n', ('h2', title)], align="center"))
        widgets.append(urwid.Text(content))

    pager = urwid.ListBox(widgets)
    pager._command_map['k'] = 'cursor up'
    pager._command_map['j'] = 'cursor down'
    pager._command_map['ctrl b'] = 'cursor page up'
    pager._command_map['ctrl f'] = 'cursor page down'

    loop = urwid.MainLoop(pager, screen=screen, handle_mouse=False,
                         unhandled_input=keymapper)
    loop.run()
