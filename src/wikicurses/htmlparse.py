import re

from collections import OrderedDict
from bs4 import BeautifulSoup

from wikicurses import formats
from wikicurses import settings

skipclass = ('wiki-sidebar', 'infobox', 'mw-editsection', 'editsection',
             'wikitable', 'thumb', 'gallery', 'article-thumb',
             'mw-headline-anchor')
skipsection = ('Contents', 'External links', 'See also')

if settings.hide_references:
    skipclass += ('reference',)
    skipsection += ('References',)

class UrwidMarkupHandler:

    def __init__(self):
        self._list = []
        self._oldlist = None

    def add(self, text, attribute):
        if not text:
            return
        if self and self[-1][0] == attribute:
            self[-1][1] += text
        else:
            self._list.append([attribute, text])

    def search(self, findtext):
        self.unsearch()
        self._oldlist = self._list
        self._list = []
        for attribute, text in self._oldlist:
            cur = 0
            if isinstance(attribute, str):
                self.add(text, attribute)
                continue
            for match in re.finditer(findtext, text):
                start, end = match.start(), match.end()
                self.add(text[cur:start], attribute)
                self.add(text[start:end], attribute | formats.searchresult)
                cur = end
            if text[cur:]:
                self.add(text[cur:], attribute)

    def unsearch(self):
        if self._oldlist:
            self._list = self._oldlist
            self._oldlist = None

    def __iter__(self):
        return (tuple(i) for i in self._list)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]


def _processExtractSection(section):
    items = UrwidMarkupHandler()
    for i in section:
        if isinstance(i, str):
            strings = (i,)
        else:
            if i.name == 'h2' or i.find('h2'):
                break
            strings = i.strings
        for item in strings:
            partags = {i.name for i in item.parents}
            tformat = sum(
                formats[i] for i in set(i.name for i in formats).intersection(partags))
            if [i for i in partags if re.fullmatch('h[3-6]', i)]:
                tformat |= formats.h
            items.add(item, tformat)
    if items:
        items[0][1] = items[0][1].lstrip()
        items[-1][1] = items[-1][1].rstrip() + '\n\n'
    return items


def parseExtract(html):
    """Parse article html and return OrderedDict of sections."""
    html = html.replace('\t', ' ')
    sections = OrderedDict()
    soup = BeautifulSoup(html, 'lxml')
    # Turn into tuple since the iterator is being modified
    for i in tuple(soup.strings):
        if 'pre' not in (j.name for j in i.parents):
            i.replace_with(i.replace('\n', ''))
    for i in soup.find_all('p'):
        i.insert_after(soup.new_string('\n\n'))
    for i in soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'br']):
        i.insert_after(soup.new_string('\n'))
    for i in soup.find_all('div'):
        if i.text and not i.find_all('div'):
            i.insert_after(soup.new_string('\n'))
    for i in soup.find_all('li'):
        if i.parent.name == 'ol':
            num = i.parent.find_all('li').index(i) + 1
            i.insert_before(soup.new_string(str(num) + '. '))
        else:
            i.insert_before(soup.new_string('• '))
        i.insert_after(soup.new_string('\n'))
        if 'li' not in (j.name for j in i.next_siblings): # Last item in list
            i.insert_after(soup.new_string('\n'))
    for i in soup.find_all(True, class_=skipclass):
        i.decompose()
    sections[''] = _processExtractSection(soup.body or soup)
    for i in soup.find_all('h2'):
        if i.text not in skipsection:
            sections[i.text.strip()] = _processExtractSection(i.next_siblings)
    for i in sections:
        if not sections[i]:
            del sections[i]
    return sections


def parseFeature(html):
    """Parse featured feed html by striping out html tags."""
    return BeautifulSoup(html, 'lxml').text


def _processDisambigSection(section):
    items = []
    for i in section:
        if isinstance(i, str):
            continue
        if i.name == 'h2' or i.find('h2'):
            break
        for item in i.find_all('li'):
            items.append(
                (item.a.text if item.a else '', item.text.split('\n')[0]))
    return items


def parseDisambig(html):
    """Parse disambiguation page and return list of (article, text) tuples."""
    sections = OrderedDict()
    soup = BeautifulSoup(html, 'lxml')
    for i in soup.find_all(True, class_=skipclass):
        i.decompose()
    sections[''] = _processDisambigSection(soup)
    for i in soup.find_all('h2'):
        if i.text not in ('Contents', 'See also'):
            sections[i.text] = _processDisambigSection(i.next_siblings)
    return sections
