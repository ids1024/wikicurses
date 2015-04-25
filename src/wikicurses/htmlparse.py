import re
from collections import OrderedDict

import bs4

from wikicurses import formats
from wikicurses import settings

skipclass = ('wiki-sidebar', 'infobox', 'mw-editsection', 'editsection',
             'wikitable', 'thumb', 'gallery', 'article-thumb', 'infobox_v2',
             'mw-headline-anchor', 'toc', 'noprint', 'wikia-gallery')
skipsection = ('External links', 'See also')

if settings.hide_references:
    skipclass += ('reference',)
    skipsection += ('References',)


def parseArticle(html):
    """Parse article html and return list of  (format, text) tuples."""
    html = html.replace('\t', ' ')
    soup = bs4.BeautifulSoup(html, 'lxml')
    # Turn into tuple since the iterator is being modified
    for i in tuple(soup.strings):
        if not {'pre', 'code'}.intersection(j.name for j in i.parents):
            i.replace_with(i.replace('\n', ''))
    for i in soup.find_all('p'):
        i.insert_after(soup.new_string('\n\n'))
    for i in soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'br', 'pre']):
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
    for i in soup.find_all('script'):
        i.decompose()
    for i in soup.find_all('h2'):
        if i.text in skipsection:
            for j in tuple(i.next_elements):
                # Test it is not a str to avoid using str.find() by accident
                if not isinstance(j, str) and (j.name == 'h2' or j.find('h2')):
                    break
                j.extract()
            i.decompose()

    items = []
    for item in soup.strings:
        if not item:
            continue

        if isinstance(item, bs4.element.Comment):
            continue # Strip out html comments

        partags = {i.name for i in item.parents}
        tformat = sum(
            formats[i] for i in set(i.name for i in formats).intersection(partags))
        if [i for i in partags if re.fullmatch('h[3-6]', i)]:
            tformat |= formats.h
        # Make <strong>/<em> use same formats as <b>/<i>
        if 'strong' in partags:
            tformat |= formats.b
        if 'em' in partags:
            tformat |= formats.i

        # Handle divs with padding or borders defined in css style
        styledivs = item.findParents('div', style=True)
        stylekeys = [i.split(':', 1)[0].strip()
                for div in styledivs for i in div.get('style').split(';')]
        if 'padding' in stylekeys:
            tformat |= formats.divpadding
        if 'border' in stylekeys:
            tformat |= formats.divborder

        # Added specifically for handling spaces between removed references
        if items and items[-1][1] and (items[-1][1][-1] == item[0] == ' '):
            item = item[1:]

        # If format same as previous, combine
        if items and items[-1][0] == tformat:
            items[-1][1] += str(item)
        else:
            items.append([tformat, str(item)])

    return items


def parseFeature(html):
    """Parse featured feed html by striping out html tags."""
    # TODO: Support html tags like <b>
    text = bs4.BeautifulSoup(html, 'lxml').text.strip() + '\n\n'
    text = re.sub('\n\n+', '\n\n', text)
    return text


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
    soup = bs4.BeautifulSoup(html, 'lxml')
    for i in soup.find_all(True, class_=skipclass):
        i.decompose()
    sections[''] = _processDisambigSection(soup)
    for i in soup.find_all('h2'):
        if i.text not in ('Contents', 'See also'):
            sections[i.text] = _processDisambigSection(i.next_siblings)
    return sections
