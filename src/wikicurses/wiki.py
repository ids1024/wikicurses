import json
import urllib.request
import re

from wikicurses.htmlparse import parseExtract
from wikicurses import wikis

image_url = "http://en.wikipedia.org/wiki/"

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

    def get_content(self):
        extract = self.page.get('extract')
        if extract is None:
            return {'':'No wikipedia page for that title.\n'
                    'Wikipedia search titles are case sensitive.'}
        sections = parseExtract(extract)
        sections.pop("External links", '')
        sections.pop("References", '')

        images = (image_url + i['title'].replace(' ', '_')
                 for i in self.page.get('images', ()))

        extlinks = (i['*'] for i in self.page['extlinks'])
        #if an url starts with //, it can by http or https.  Use http.
        extlinks = ('http:' + i if i.startswith('//') else i for i in extlinks)

        iwlinks = (wikis[i['prefix']].replace('$1', i['*'])
                  for i in self.page['iwlinks'] if i['prefix'] in wikis)

        sections.update({
            'Images':'\n'.join(images) + '\n',
            'External links':'\n'.join(extlinks) + '\n',
            'Interwiki links':'\n'.join(iwlinks) + '\n'
            })
        return sections