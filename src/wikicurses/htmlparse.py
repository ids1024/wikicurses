import re

from collections import OrderedDict
from html.parser import HTMLParser

from wikicurses import formats

ENDPAR, STARTPAR, ENDH = range(3)

def parseExtract(html):
    parser = _ExtractHTMLParser()
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

    def add_text(self, text):
        if text == ENDPAR:
            if self.format&formats.blockquote:
                return
            text = '\n'
        elif text == STARTPAR:
            if self.format&formats.blockquote:
                text = '\n> '
            else:
                return
        elif text == ENDH:
            text = '\n'

        tformat = self.format

        if self.inh and text in ('[', ']', 'edit'):
            return
        if self.inh == 2:
            self.cursection += text
            return
        elif self.inh > 2:
            tformat = 'h'
        if self.cursection not in self.sections:
            self.sections[self.cursection] = []
        section = self.sections[self.cursection]
        if section and section[-1][0] == tformat:
            section[-1] = (section[-1][0], section[-1][1] + text)
        else:
            section.append((tformat, text))

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.cursection = ''
        if re.fullmatch("h[2-6]", tag):
            self.inh = int(tag[1:])
        elif tag == 'p':
            self.add_text(STARTPAR)
        elif tag == 'li':
            self.add_text("- ")
        elif tag in (i.name for i in formats):
            self.format|=formats[tag]

    def handle_endtag(self, tag):
        if re.fullmatch("h[2-6]", tag):
            self.inh = 0
            self.add_text(ENDH)
        elif tag == 'p':
            self.add_text(ENDPAR)
        elif tag in (i.name for i in formats):
            self.format&=~formats[tag]
        if tag == 'blockquote':
            self.add_text(ENDPAR)

    def handle_data(self, data):
        self.add_text(re.sub('\n+', '\n', data))


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
        if self.inh2 and data not in ('[', ']', 'edit'):
            self.cursection += data
        if self.ina:
            self.a += data
        if self.inli:
            self.li += data
