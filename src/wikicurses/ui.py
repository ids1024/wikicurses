import urwid

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

    screen = urwid.raw_display.Screen() 
    screen.register_palette_entry('h1', 'yellow,bold', '')
    screen.register_palette_entry('h2', 'underline', '')
    screen.register_palette_entry('h', 'underline', '')
    #screen.register_palette_entry('italic', 'italics', '') #No italics option?
    screen.register_palette_entry('bold', 'bold', '')
    screen.register_palette_entry('bolditalic', 'bold', '')
    screen.register_palette_entry('blockquote', 'dark gray', '')

    def keymapper(input):
        #TODO: Implement gg and G
        if input == 'q':
            raise  urwid.ExitMainLoop
        else:
            return False
        return True

    loop = urwid.MainLoop(pager, screen=screen, handle_mouse=False,
                         unhandled_input=keymapper)
    loop.run()
