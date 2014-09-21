import re

from collections import OrderedDict
from html.parser import HTMLParser

ENDPAR = 1
STARTPAR = 2

def parseExtract(html):
    parser = _ExtractHTMLParser()
    parser.feed(html)
    return parser.sections

def parseFeature(html):
    parser = _FeatureHTMLParser()
    parser.feed(html)
    return parser.text

class _ExtractHTMLParser(HTMLParser):
    cursection = ''
    inh = 0
    inblockquote = False
    bold = False
    italic = False

    def __init__(self):
        self.sections = OrderedDict({'':[]})
        super().__init__(self)

    def add_text(self, text):
        if text == ENDPAR:
            if self.inblockquote:
                return
            text = '\n\n'
        elif text == STARTPAR:
            if self.inblockquote:
                text = '\n> '
            else:
                return
        elif not text.strip():
            return

        if self.inblockquote:
            tformat = "blockquote"
        elif self.bold and self.italic:
            tformat = "bolditalic"
        elif self.bold:
            tformat = "bold"
        elif self.italic:
            tformat = "italic"
        else:
            tformat = ''

        if self.inh == 2:
            self.cursection += text
        elif self.inh > 2:
            self.sections[self.cursection].append(('h', text+'\n'))
        else:
            self.sections[self.cursection].append((tformat, text))

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            #Remove previous section if empty
            if not self.sections[self.cursection]:
                del self.sections[self.cursection]
            self.inh = 2
            self.cursection = ''
        elif re.fullmatch("h[3-6]", tag):
            self.inh = int(tag[1:])
        elif tag == 'i':
            self.italic = True
        elif tag == 'b':
            self.bold = True
        elif tag == 'p':
            self.add_text(STARTPAR)
        elif tag == 'li':
            self.add_text("- ")
        elif tag == 'blockquote':
            self.inblockquote = True

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.inh = 0
            self.sections[self.cursection] = []
        elif re.fullmatch("h[3-6]", tag):
            self.inh = 0
        elif tag == 'i':
            self.italic = False
        elif tag == 'b':
            self.bold = False
        elif tag == 'p':
            self.add_text(ENDPAR)
        elif tag == 'blockquote':
            self.inblockquote = False

    def handle_data(self, data):
        text = data.replace('*', '\\*')
        text = re.sub('\n+', '\n', text)
        self.add_text(text)


class _FeatureHTMLParser(HTMLParser):
    text = ''
    def handle_data(self, data):
        self.text += data
