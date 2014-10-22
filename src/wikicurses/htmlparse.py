import re

from collections import OrderedDict
from html.parser import HTMLParser

from wikicurses import formats

def parseExtract(html):
    parser = _ExtractHTMLParser()
    html = re.sub('\n+', '\n', html).replace('\t', ' ')
    parser.feed(html)
    for i in parser.sections:
        if not parser.sections[i]:
            del parser.sections[i]
    return parser.sections

def parseFeature(html):
    parser = _FeatureHTMLParser()
    parser.feed(html)
    return parser.text

def parseDisambig(html):
    parser = _DisambigHTMLParser()
    parser.feed(html)
    if not parser.sections['']:
        parser.sections.pop('', '')
    parser.sections.pop('Contents', '')
    parser.sections.pop('See also', '')
    return parser.sections

class _ExtractHTMLParser(HTMLParser):
    cursection = ''
    inh = 0
    format = 0

    def __init__(self):
        self.sections = OrderedDict({'':[]})
        super().__init__(self)

    def add_text(self, text, tformat=None):
        tformat = tformat or self.format
        sec = self.sections[self.cursection]

        if sec and sec[-1][0] == tformat:
            sec[-1] = (sec[-1][0], sec[-1][1] + text)
        elif len(sec) == 0:
            if text.lstrip():
                sec.append((tformat, text.lstrip()))
        else:
            sec.append((tformat, text))

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            #Remove extra trailing newlines from last section
            if self.sections[self.cursection]:
                sec = self.sections[self.cursection]
                sec[-1] = (sec[-1][0], sec[-1][1].rstrip() + '\n')
            self.cursection = ''
        if re.fullmatch("h[2-6]", tag):
            self.inh = int(tag[1:])
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
            self.sections[self.cursection] = []
        if re.fullmatch("h[2-6]", tag):
            self.inh = 0
            self.add_text('\n')
        elif tag == 'p' and not self.format&formats.blockquote:
            self.add_text('\n')
        elif tag in (i.name for i in formats):
            self.format&=~formats[tag]

    def handle_data(self, data):
        if self.inh == 2:
            self.cursection += data
        elif not (self.inh and data in ('[', ']', 'edit', 'Edit')):
            tformat = 'h' if (self.inh > 2) else self.format
            self.add_text(data, tformat)


class _FeatureHTMLParser(HTMLParser):
    text = ''
    def handle_data(self, data):
        self.text += data

class _DisambigHTMLParser(HTMLParser):
    cursection = ''
    inh2 = False
    ina = False
    inli = False
    format = 0
    li = ''
    a = ''

    def __init__(self):
        self.sections = OrderedDict({'':[]})
        super().__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.cursection = ''
            self.inh2 = True
        elif tag == 'li':
            if self.inli:
                self.sections[self.cursection].append((self.a, self.li.strip()))
                self.li = ''
                self.a = ''
            self.inli = True
        elif tag == 'a' and self.inli:
            self.ina = True

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.inh2 = False
            self.sections[self.cursection] = []
        elif tag == 'li':
            self.inli = False
            if self.li:
                self.sections[self.cursection].append((self.a, self.li.strip()))
                self.li = ''
                self.a = ''
        elif tag == 'a' and self.ina:
            self.ina = False

    def handle_data(self, data):
        if self.inh2 and data not in ('[', ']', 'edit', 'Edit'):
            self.cursection += data
        if self.ina:
            self.a += data
        if self.inli:
            self.li += data
