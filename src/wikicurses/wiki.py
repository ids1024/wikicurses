import json
import urllib.request
import re
import  xml.etree.ElementTree as ET
from collections import OrderedDict

from wikicurses.htmlparse import parseExtract, parseFeature
from wikicurses import wikis

image_url = "http://en.wikipedia.org/wiki/"
base_url = "http://en.wikipedia.org/w/api.php?"

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
        data = {"action":"featuredfeed", "feed":feed}
        result = ET.fromstring(self._query(data))
        return _Featured(feed, result)


class _Article(object):
    def __init__(self, result):
        self.page = next(iter(result['query']['pages'].values()))
        self.title = self.page['title']

    @property
    def content(self):
        if 'extract' not in self.page:
            return {'':'Page Not Found.'}
        sections = parseExtract(self.page['extract'])
        sections.pop("External links", '')
        sections.pop("References", '')

        images = (image_url + i['title'].replace(' ', '_')
                 for i in self.page.get('images', ()))

        extlinks = (i['*'] for i in self.page.get('extlinks', ()))
        #if an url starts with //, it can by http or https.  Use http.
        extlinks = ('http:' + i if i.startswith('//') else i for i in extlinks)

        iwlinks = (wikis[i['prefix']].replace('$1', i['*'])
                  for i in self.page.get('iwlinks', ()) if i['prefix'] in wikis)

        sections.update({
            'Images':'\n'.join(images) + '\n',
            'External links':'\n'.join(extlinks) + '\n',
            'Interwiki links':'\n'.join(iwlinks) + '\n'
            })
        return sections


class _Featured(object):
    def __init__(self, feed, result):
        self.feed = feed
        self.result = result
        self.title = {'onthisday': 'On this Day',
                'featured': 'Featured Articles',
                'potd': 'Picture of the Day'
                }[feed]

    @property
    def content(self):
        sections = OrderedDict()
        for i in self.result[0].findall('item'):
            description = i.findtext('description')
            if self.feed == 'onthisday':
                htmls = re.findall("<li>(.*?)</li>", description, flags=re.DOTALL)
                text = '\n'.join(map(parseFeature, htmls))
            else:
                text = parseFeature(description)
            sections[i.findtext('title')] = i.findtext('link') + '\n' + text
        return sections


wiki = Wiki(base_url)
