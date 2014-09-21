import json
import urllib.request
import re

from wikicurses.htmlparse import parseExtract
from wikicurses import wikis

class Wiki(object):
    def __init__(self, url):
        self.siteurl = url

    def _query(self, data):
        url = self.siteurl + urllib.parse.urlencode(data)
        # open url, read content (bytes), convert in string via decode()
        return urllib.request.urlopen(url).read().decode('utf-8')

    def search(self, titles):
        data = {"action":"query", "prop":"extracts|info|extlinks|images|iwlinks",
                "titles":titles, "redirects":True, "format":"json",
                "inprop":"url|displaytitle"}
        result = json.loads(self._query(data))
        return _Article(result)

    def get_featured_feed(self, feed):
        """Featured Feed"""

        data = {"action":"featuredfeed", "feed":feed, "format": "json"}
        result = self._query(data)

        re_title = re.compile('<title>(.*)</title>')
        re_links = re.compile('<link>(.*)en</link>')

        result1 = re.findall(re_title, result)
        result2 = re.findall(re_links, result)

        return '\n' + ''.join('%s:\t %s' % i for i in zip(result1, result2))


class _Article(object):
    def __init__(self, result):
        # In python 3 dict_keys are not indexable, so we need to use list()
        key = list(result['query']['pages'])[0][:]
        self.page = result['query']['pages'][key]
        self.title = self.page['title']

    def _get_extract(self):
        """ Get extract """
        extract = self.page.get('extract')
        if extract is None:
            sections ={'':'No wikipedia page for that title.\n'
                      'Wikipedia search titles are case sensitive.'}
        else:
            sections = parseExtract(extract)
        sections.pop("External links", '')
        sections.pop("References", '')
        return sections

    def _get_external_links(self):
        """ Get external links """
        try:
            extlinks = self.page['extlinks']
        except KeyError:
            return ''
        links = (i['*'] for i in extlinks)
        return ''.join(('http:' + i if i.startswith('//') else i) + '\n'
                for i in links)

    def _get_interwiki_links(self):
        """ Inter wiki links """
        try:
            iwlinks = self.page['iwlinks']
        except KeyError:
            return ''
        return ''.join(wikis[i['prefix']].replace('$1', i['*']) + '\n'
                for i in self.page['iwlinks'] if i['prefix'] in wikis)

    def _get_images(self):
        """ Get images urls """

        image_url = "http://en.wikipedia.org/wiki/"

        return ''.join(image_url + i['title'].replace(' ', '_') + '\n'
                for i in self.page.get('images', ()))

    def get_content(self):
        sections = self._get_extract()
        sections.update({
            'Images\n':self._get_images(),
            '\nExternal links\n':self._get_external_links(),
            '\nInterwiki links\n':self._get_interwiki_links()
            })
        return sections
