import re

from collections import OrderedDict
from html.parser import HTMLParser

class ExcerptHTMLParser(HTMLParser):
    sections = OrderedDict({'':[]})
    cursection = ''
    inh2 = False
    inblockquote = False
    bold = False
    italic = False

    def add_text(self, text):
        if self.bold and self.italic:
            tformat = "bolditalic"
        elif self.bold:
            tformat = "bold"
        elif self.italic:
            tformat = "italic"
        else:
            tformat = ''
        if self.inh2:
            self.cursection += text
        elif self.inblockquote:
            self.sections[self.cursection].append((tformat, '> ' + text))
        else:
            self.sections[self.cursection].append((tformat, text))

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.inh2 = True
            self.cursection = ''
        elif re.fullmatch("h[3-6]", tag):
            self.add_text('\n')
        elif tag == 'i':
            self.italic = True
        elif tag == 'b':
            self.bold = True
        elif tag == 'li':
            self.add_text("- ")
        elif tag == 'blockquote':
            self.inblockquote = True
        else:
            pass

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.inh2 = False
            self.sections[self.cursection] = []
        elif re.fullmatch("h[3-6]", tag):
            self.add_text('\n')
        elif tag == 'i':
            self.italic = False
        elif tag == 'b':
            self.bold = False
        elif tag == 'p':
            self.add_text('\n')
        elif tag == 'blockquote':
            self.inblockquote = False
        else:
            pass

    def handle_data(self, data):
        text = data.replace('*', '\\*')
        text = re.sub('\n+', '\n', text)
        self.add_text(text)
