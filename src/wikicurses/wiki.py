import json
import urllib.request
import re
import  xml.etree.ElementTree as ET
from collections import OrderedDict

from wikicurses.htmlparse import parseExtract, parseFeature

image_url = "http://en.wikipedia.org/wiki/"
base_url = "http://en.wikipedia.org/w/api.php?"

class Wiki(object):
    def __init__(self, url):
        self.siteurl = url

    def _query(self, **data):
        url = self.siteurl + urllib.parse.urlencode(data)
        return urllib.request.urlopen(url).read().decode('utf-8')

    def search(self, titles):
        result = self._query(action="query", redirects=True, titles=titles, 
                    prop="extracts|info|extlinks|images|iwlinks",
                    meta="siteinfo", siprop="interwikimap",
                    inprop="url|displaytitle", format="json")
        return _Article(json.loads(result))

    def get_featured_feed(self, feed):
        result = self._query(action="featuredfeed", feed=feed)
        return _Featured(feed, ET.fromstring(result)[0])


class _Article(object):
    def __init__(self, result):
        self.interwikimap = {i['prefix']: i['url'] 
                for i in result['query']['interwikimap']}
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

        iwlinks = (self.interwikimap[i['prefix']].replace('$1', i['*'])
                  for i in self.page.get('iwlinks', ())
                  if i['prefix'] in self.interwikimap)

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
        self.title = result.find('title').text

    @property
    def content(self):
        sections = OrderedDict()
        for i in self.result.findall('item'):
            description = i.findtext('description')
            if self.feed == 'onthisday':
                htmls = re.findall("<li>(.*?)</li>", description, flags=re.DOTALL)
                text = '\n'.join(map(parseFeature, htmls))
            else:
                text = parseFeature(description)
            sections[i.findtext('title')] = i.findtext('link') + '\n' + text
        return sections


wiki = Wiki(base_url)
