import re

from collections import OrderedDict
from html.parser import HTMLParser
from bs4 import BeautifulSoup

from wikicurses import formats

class UrwidMarkupHandler:
    def __init__(self):
        self._list = []

    def add(self, text, attribute):
        if self and self[-1][0] == attribute:
            self[-1][1] += text
        else:
            self._list.append([attribute, text])

    def __iter__(self):
        return map(tuple, self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]

def parseExtract(html):
    parser = _ExtractHTMLParser()
    html = re.sub('\n+', '\n', html).replace('\t', ' ')
    parser.feed(html)
    for i in parser.sections:
        if not parser.sections[i]:
            del parser.sections[i]
    parser.sections.pop("External links", '')
    parser.sections.pop("References", '')
    parser.sections.pop("Contents", '')
    return parser.sections

def parseFeature(html):
    return BeautifulSoup(html).text

def parseDisambig(html):
    sections = OrderedDict()
    soup = BeautifulSoup(html)
    for i in soup.find_all('h2'):
        title = re.sub('\[edit\]$', '', i.text)
        if title in ('Contents', 'See also'):
            continue
        items = []
        for j in i.next_siblings:
            if j.name == 'h2':
                break
            if isinstance(j, str):
                continue
            for item in j.find_all('li'):
                items.append((item.a.text if item.a else '', item.text.split('\n')[0]))
        sections[title] = items
    return sections

class _ExtractHTMLParser(HTMLParser):
    cursection = ''
    inh = 0
    insidebar = False
    format = 0

    def __init__(self):
        self.sections = OrderedDict({'':UrwidMarkupHandler()})
        super().__init__(self)

    def add_text(self, text, tformat=None):
        sec = self.sections[self.cursection]
        sec.add(text, tformat or self.format)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split(' ')
        if tag == 'h2':
            #Remove extra trailing newlines from last section
            sec = self.sections[self.cursection]
            if sec:
                sec[-1][1] = sec[-1][1].rstrip() + '\n'
            self.cursection = ''
        if re.fullmatch("h[2-6]", tag):
            self.inh = int(tag[1:])
        elif tag == 'table' \
                and ('wiki-sidebar' in classes or 'infobox' in classes):
            self.insidebar = True
        elif tag == 'p' and self.format&formats.blockquote:
            self.add_text('> ')
        elif tag == 'br':
            self.add_text('\n')
        elif tag == 'li':
            self.add_text("- ")
        elif tag in (i.name for i in formats):
            self.format|=formats[tag]

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.cursection = self.cursection.strip()
            self.sections[self.cursection] = UrwidMarkupHandler()
        if re.fullmatch("h[2-6]", tag):
            self.inh = 0
            self.add_text('\n')
        elif tag == 'table':
            self.insidebar = False
        elif tag == 'p' and not self.format&formats.blockquote:
            self.add_text('\n')
        elif tag in (i.name for i in formats):
            self.format&=~formats[tag]

    def handle_data(self, data):
        if self.inh and data in ('[', ']', 'edit', 'Edit'):
            pass
        elif self.insidebar:
            pass
        elif self.inh == 2:
            self.cursection += data
        else:
            tformat = 'h' if (self.inh > 2) else self.format
            if not self.sections[self.cursection]:
                data = data.lstrip()
            self.add_text(data, tformat)
