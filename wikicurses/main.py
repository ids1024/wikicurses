import os
import re
import argparse
import tempfile
import subprocess
import urllib.parse

import urwid

from wikicurses import formats, settings
from wikicurses.wiki import Wiki, WikiError
from wikicurses.htmlparse import parseDisambig


def executeCommand(cmd):
    try:
        subprocess.call(cmd)
    except FileNotFoundError:
        ex.notify("Error: command '" + cmd[0] + "' not found.")
    loop.screen.clear() # Completely redraw screen after external command


def setTerminalWindowTitle(title):
    print('\33]0;' + title + ' - wikicurses\a')


def tabComplete(text, matches):
    if not matches:
        return text
    matches = sorted(matches, key=len)
    if matches[0] == text and len(matches) > 1:
        match = matches[1]
    else:
        match = matches[0]
    return match


class SearchBox(urwid.Edit):
    title = "Search"

    def keypress(self, size, key):
        if key == 'enter':
            closeOverlay()
            openPage(self.edit_text)
        elif key == 'tab':
            matches = wiki.search_sugestions(self.edit_text)
            match = tabComplete(self.edit_text, matches)
            self.edit_text = match
            self.edit_pos = len(match)
        elif key == 'esc':
            closeOverlay()
        else:
            return super().keypress(size, key)


class SelectorBox(urwid.ListBox):

    def __init__(self):
        def selectButton(radio_button, new_state, parameter):
            if new_state:
                closeOverlay()
                self._select(parameter)

        super().__init__(urwid.SimpleFocusListWalker([]))
        buttons = []
        for i, item in enumerate(self._items()):
            if isinstance(item, urwid.Widget):
                self.body.append(item)
                continue
            elif isinstance(item, tuple):
                name, selected, parameter = item
            else:
                parameter = name = item
                selected = False
            self.body.append(urwid.RadioButton(buttons, name, selected,
                                               selectButton, parameter))
            if selected:
                self.set_focus(i)

    def keypress(self, size, key):
        if key == 'esc':
            closeOverlay()
        else:
            return super().keypress(size, key)


class Toc(SelectorBox):
    title = "Table of Contents"

    def _items(self):
        for name, ind in mainwidget.body.widgetnames:
            yield name, mainwidget.body.body.focus >= ind, ind

    def _select(self, index):
        mainwidget.body.body.set_focus(index)


class Bmarks(SelectorBox):
    title = "Bookmarks"

    def _items(self):
        self.deleted = []
        return wiki.bmarks

    def _select(self, name):
        openPage(name)

    def keypress(self, size, key):
        # Undo Delete
        if key == 'u' and self.deleted:
            index, item = self.deleted.pop()
            wiki.bmarks.add(item.label)
            self.body.insert(index, item)
            self.set_focus(index)
        elif key in ('meta [', 'x') and self.focus:
            wiki.bmarks.discard(self.focus.label)
            self.deleted.append((self.focus_position, self.focus))
            self.body.remove(self.focus)
        else:
            return super().keypress(size, key)


class Links(SelectorBox):
    title = "Links"

    def _items(self):
        return page.links

    def _select(self, name):
        openPage(name)


class Iwlinks(SelectorBox):
    title = "Interwiki Links"

    def _items(self):
        netlocname = [(urllib.parse.urlparse(url).netloc, name)
                       for name, url in page.iwlinks]
        netlocs = set(netloc for netloc, name in netlocname)
        for netloc in netlocs:
            yield urwid.Text(netloc)
            # If the name in blank, the link refers to the site's Main Page
            yield from (j or "Main page" for i, j in netlocname if i == netloc)

    def _select(self, name):
        if name == "Main page":
            name = ''
        url = dict(page.iwlinks)[name]
        openWiki(Wiki.fromPageUrl(url))
        openPage(name)


class Langs(SelectorBox):
    title = "Languages"

    def _items(self):
        return page.langlinks.keys()

    def _select(self, lang):
        url, name = page.langlinks[lang]
        openWiki(Wiki.fromPageUrl(url))
        openPage(name)


class Extlinks(SelectorBox):
    title = "External Links"

    def _items(self):
        return page.extlinks

    def _select(sel, url):
        executeCommand([os.environ.get('BROWSER', 'lynx'), url])


class Wikis(SelectorBox):
    title = "Wikis"

    def _items(self):
        for name, url in settings.wikis().items():
            yield name, wiki.siteurl == url, name

    def _select(self, name):
        openWiki(name)
        openPage()


class Feeds(SelectorBox):
    title = "Feeds"

    def _items(self):
        return wiki.list_featured_feeds()

    def _select(self, feed):
        openPage(feed, True)


class Ex(urwid.Edit):
    mode = None
    highlighted = ''

    def highlightText(self, text):
        self.highlighted = text
        if text:
            mainwidget.body.search(text)
        else:
            mainwidget.body.unsearch()

    def keypress(self, size, key):
        if key == 'esc' or (key == 'backspace' and not self.edit_text):
            if self.mode == 'search':
                self.highlightText(self.previous_highlight)
            self.exitexmode()
        elif key == 'tab' and self.mode == 'ex':
            matches = [i for i in cmds if i.startswith(self.edit_text)]
            match = tabComplete(self.edit_text, matches)
            self.edit_text = match
            self.edit_pos = len(match)
        elif key == 'enter':
            if self.mode == 'ex':
                matches = [i for i in cmds if i.startswith(self.edit_text)]
                match = tabComplete(self.edit_text, matches)
                processCmd(*match.split())
            if self.mode == 'search':
                self.highlightText(self.edit_text)
            self.exitexmode()
        else:
            returnval = super().keypress(size, key)
            # Highlight after running super().keypress() so that edit_text is
            # up to date.
            if self.mode == 'search':
                self.highlightText(self.edit_text)
            return returnval

    def exitexmode(self):
        self.set_caption('')
        self.set_edit_text('')
        mainwidget.set_focus('body')
        self.mode = None

    def enterexmode(self):
        mainwidget.set_focus('footer')
        self.set_caption(':')
        self.mode = 'ex'

    def entersearchmode(self):
        self.previous_highlight = self.highlighted
        mainwidget.set_focus('footer')
        self.set_caption('/')
        self.mode = 'search'

    def notify(self, text):
        self.set_edit_text(text)


class StandardKeyBinds:

    def keypress(self, size, key):
        returnval = None
        maxcol, maxrow = size
        ex.notify('') # Clear any notification

        cmdmap = settings.conf['keymap']
        if key == ':':
            ex.enterexmode()
        if key == '/':
            # Disable search for Disambig/Results page
            if isinstance(mainwidget.body, Pager):
                ex.entersearchmode()
        elif key in ('g', 'home'):
            self.change_focus(size, 0, 0)
        elif key in ('G', 'end'):
            self.change_focus(size, len(self.body) - 1)
            offset = maxrow - self.focus.rows((maxcol,))
            self.change_focus(size, len(self.body) - 1, offset)
        elif key in cmdmap and cmdmap[key]:
            processCmd(cmdmap[key])
        else:
            returnval = super().keypress(size, key)

        # Set progress percentage
        lens = [i.rows((maxcol,)) for i in self.body]
        offset, inset = self.get_focus_offset_inset(size)
        # Number of the first line on the screen
        current_line = sum(lens[:self.body.focus]) - offset + inset
        position = current_line / (sum(lens) - maxrow) * 100
        progress.set_text(str(round(position)) + '%')

        return returnval

    def mouse_event(self, size, event, button, col, row, focus):
        if button == 4:
            self.keypress(size, 'up')
        if button == 5:
            self.keypress(size, 'down')
        else:
            return super().mouse_event(size, event, button, col, row, focus)
        return True


class Disambig(StandardKeyBinds, SelectorBox):
    widgetnames = []

    def __init__(self, html):
        self.sections = parseDisambig(html)
        super().__init__()

    def _items(self):
        for title, items in self.sections.items():
            if title:
                yield urwid.Text(['\n', ('h', title)], align='center')
            for name, text in items:
                yield (text, False, name) if name else urwid.Text(text)

    def _select(self, name):
        openPage(name)


class Results(StandardKeyBinds, SelectorBox):
    widgetnames = []

    def __init__(self, results):
        self.results = results
        super().__init__()

    def _items(self):
        return self.results

    def _select(self, title):
        openPage(title)


class Pager(StandardKeyBinds, urwid.ListBox):

    def __init__(self, page):
        super().__init__(urwid.SimpleFocusListWalker([]))
        self._content = page.content.copy()
        self._render()

    def _render(self):
        self.body.clear()
        self.widgetnames = [(page.title, 0)]
        curtext = []
        curh2 = ''
        prevalign = 'left'
        prevpadding = 0
        prevborder = False
        for tformat, text in self._content:
            align = settings.getColor(tformat, 'align', default='left')
            padding = settings.getColor(tformat, 'padding', default=0)
            border = settings.getColor(tformat, 'border', default=False)

            if (((align, padding, border) != (prevalign, prevpadding, prevborder)
                    and curtext) or (tformat & formats.h2 and not curh2)):
                # Also have new Text() for every h2 for TOC
                widget = urwid.Text(curtext, align=prevalign)
                if prevborder:
                    widget = urwid.LineBox(widget)
                if prevpadding:
                    widget = urwid.Padding(widget,
                        left=prevpadding, right=prevpadding)
                self.body.append(widget)
                curtext.clear()
            
            curtext.append((tformat, text))

            if tformat & formats.h2: 
                curh2 += text
            elif curh2:
                self.widgetnames.append((curh2, len(self.body) - 1))
                curh2 = ''

            prevalign = align
            prevpadding = padding
            prevborder = border
        if curtext:
            widget = urwid.Text(curtext, align=prevalign)
            if prevborder:
                widget = urwid.LineBox(widget)
            if prevpadding:
                widget = urwid.Padding(widget,
                    left=prevpadding, right=prevpadding)
            self.body.append(widget)

    def _add(self, text, attribute):
        if text:
            if self._content and self._content[-1][0] == attribute:
                self._content[-1][1] += text
            else:
                self._content.append([attribute, text])

    def search(self, findtext):
        self._content.clear()
        for attribute, text in page.content:
            cur = 0
            for match in re.finditer(findtext, text):
                start, end = match.start(), match.end()
                self._add(text[cur:start], attribute)
                self._add(text[start:end], attribute | formats.searchresult)
                cur = end
            if text[cur:]:
                self._add(text[cur:], attribute)
        self._render()

    def unsearch(self):
        self._content = page.content.copy()
        self._render()


def openPage(title=None, featured=False, browsinghistory=False):
    if not title:
        title = wiki.mainpage

    if not browsinghistory:
        global current
        if current < len(history)-1:
            del history[current+1:len(history)]
        history.append(title)
        current += 1

    global page
    if featured:
        page = wiki.get_featured_feed(title)
    else:
        page = wiki.search(title)
    # This is not as inefficient as it looks; Wiki caches results
    if not page.exists and wiki.search_sugestions(page.title):
        header.set_text('Results for ' + title)
        mainwidget.body = Results(wiki.search_sugestions(page.title))
    elif 'disambiguation' in page.properties:
        header.set_text(page.title + ': Disambiguation')
        mainwidget.body = Disambig(page.html)
    else:
        header.set_text(page.title)
        mainwidget.body = Pager(page)

    setTerminalWindowTitle(title)
    progress.set_text('0%')


def openWiki(name):
    global wiki
    if isinstance(name, Wiki):
        wiki = name
        return
    if not name:
        name = settings.conf['general']['default']
    if name in settings.conf:
        wiki = Wiki.fromName(name)
    else:
        wiki = Wiki.fromApiUrl(name)


def runEditor(text):
    with tempfile.NamedTemporaryFile('w+') as file:
        file.write(text)
        file.flush()
        executeCommand([os.environ.get('EDITOR', 'vim'), file.name])
        file.seek(0)
        return file.read()


def edit(title):
    try:
        text, verify = wiki.init_edit(title)
        wiki.login()

        newtext = runEditor(text)
        if newtext == text:
            ex.notify('Edit Canceled: No Change')
            return

        def submit(button):
            closeOverlay()
            wiki.commit_edit(newtext, summary.edit_text,
                             minor.get_state(), verify)
            openPage(title)
        def cancel(button):
            closeOverlay()
        summary = urwid.Edit('Summary: ')
        minor = urwid.CheckBox('Minor Edit')
        cancel_button = urwid.Button('Cancel', cancel)
        submit_button = urwid.Button('Submit', submit)
        pile = urwid.Pile([summary, minor, cancel_button, submit_button])
        openOverlay(pile, 'Edit', 'pack')
    except WikiError as e:
        ex.notify('Error: ' + str(e))

overlaymap = {'bmarks': Bmarks,
              'wikis': Wikis,
              'feeds': Feeds,
              'contents': Toc,
              'links': Links,
              'iwlinks': Iwlinks,
              'extlinks': Extlinks,
              'langs': Langs}
cmds = tuple(overlaymap) + ('quit', 'bmark', 'open', 'edit', 'clearcache',
                            'help', 'back', 'forward', 'random')

def processCmd(cmd, *args):
    global current

    if cmd in ('q', 'quit'):
        raise urwid.ExitMainLoop
    elif cmd == 'bmark':
        wiki.bmarks.add(page.title)
        ex.notify("Bookmark Added")
    elif cmd in overlaymap:
        openOverlay(overlaymap[cmd]())
    elif cmd == 'open':
        if args:
            openPage(' '.join(args))
        else:
            openOverlay(SearchBox())
    elif cmd == 'clearcache':
        wiki.clear_cache()
    elif cmd == 'edit':
        edit(page.title)
    elif cmd == 'help':
        executeCommand(['man', 'wikicurses'])
    elif cmd == 'back':
        if current > 0:
            current -= 1
            openPage(history[current], browsinghistory=True)
    elif cmd == 'forward':
        if current < len(history)-1:
            current += 1
            openPage(history[current], browsinghistory=True)
    elif cmd == 'random':
        openPage(wiki.random())
    elif cmd:
        ex.notify(cmd + ': Unknown Command')


def openOverlay(widget, title=None, height=('relative', 50), width=('relative', 50)):
    if widget.sizing() == {'flow'}:
        height = 'pack'
    box = urwid.LineBox(widget, title or widget.title)
    overlay = urwid.Overlay(box, mainwidget, 'center', width, 'middle', height)
    loop.widget = overlay


def closeOverlay():
    loop.widget = mainwidget


def main():
    parser = argparse.ArgumentParser(
        description="A simple curses interface for accessing Wikipedia.")

    parser.add_argument('search',
                        nargs='?',
                        help="page to search for")
    parser.add_argument('-w', '--wiki', help='wiki api url')
    # For shell completion functions
    parser.add_argument('--complete',
                        action='store',
                        help=argparse.SUPPRESS)
    parser.add_argument('--dumpcolors',
                        action='store_true',
                        help="print default color settings")

    parser.add_argument('-f', '--feed', help='view featured feed')

    args = parser.parse_args()
    openWiki(args.wiki)

    if args.complete:
        if args.complete == 'search':
            sugestions = wiki.search_sugestions(args.search)
        elif args.complete == 'feed':
            sugestions = wiki.list_featured_feeds()
        elif args.complete == 'wiki':
            sugestions = settings.wikis().keys()
        print(*sugestions, sep='\n')
        return
    elif args.dumpcolors:
        settings.dumpColors()
        print("Color settings written to " + settings.colorspath + '.')
        return

    callback = lambda x, y: openPage(args.feed or args.search, bool(args.feed))
    loop.set_alarm_in(.001, callback)  # Open page once loop is started
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


history = []
current = -1
page = None

palette = []
for x in range(1, sum(formats) + 1):
    fgcolor = settings.getColor(x, 'fgcolor')
    bg = settings.getColor(x, 'bgcolor')
    fgfmts = {j for i in formats if x & i and i.name in settings.colors
            for j in settings.colors[i.name][0]}
    if fgcolor:
        fgfmts.add(fgcolor)
    fg = ','.join(fgfmts)
    palette.append((x, fg, bg))

urwid.command_map['k'] = 'cursor up'
urwid.command_map['j'] = 'cursor down'
urwid.command_map['ctrl b'] = 'cursor page up'
urwid.command_map['ctrl f'] = 'cursor page down'

ex = Ex()
header = urwid.Text('Wikicurses', align='center')
loading = urwid.Filler(urwid.Text('Loading...'), 'top')
progress = urwid.Text('')
footer = urwid.Columns([ex, ('pack', progress)], 2)
mainwidget = urwid.Frame(loading, urwid.AttrMap(header, formats.h1), footer)
loop = urwid.MainLoop(mainwidget, palette=palette, handle_mouse=settings.mouse)
