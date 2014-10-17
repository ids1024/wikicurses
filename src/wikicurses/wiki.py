import json
import urllib.request
import re
import  xml.etree.ElementTree as ET
from collections import OrderedDict

from wikicurses.htmlparse import parseExtract, parseFeature

class Wiki(object):
    def __init__(self, url):
        self.siteurl = url
        self.have_siteinfo = False

    def get_siteinfo(self):
        if self.have_siteinfo:
            return
        result = self._query(action="query", meta="siteinfo",
                siprop="extensions|general", format="json")
        query = json.loads(result)["query"]

        extensions = (i["name"] for i in query["extensions"])
        self.has_extract = "TextExtracts" in extensions
        self.articlepath = urllib.parse.urljoin( 
                query['general']['base'],
                query['general']['articlepath'])
        self.have_siteinfo = True

    def _query(self, **data):
        url = self.siteurl + '?' + urllib.parse.urlencode(data)
        return urllib.request.urlopen(url).read().decode('utf-8')

    def search(self, name):
        self.get_siteinfo()
        prop = "images|externallinks|iwlinks|displaytitle"
        html = ''
        if self.has_extract:
            result = json.loads(self._query(action="query", redirects=True,
                     titles=name, prop="extracts", format="json"))['query']
            html = next(iter(result['pages'].values())).get('extract', '')
        else:
            prop += '|text'

        result = json.loads(self._query(action="parse", page=name,
                 format="json", redirects=True, prop=prop)).get('parse', {})
        if 'text' in result:
            html = result['text']['*']

        return _Article(self, name, html, result)

    def get_featured_feed(self, feed):
        result = self._query(action="featuredfeed", feed=feed)
        return _Featured(feed, ET.fromstring(result)[0])

    def search_sugestions(self, name):
        result = self._query(action="opensearch", search=name, format="json")
        return json.loads(result)[1]


class _Article(object):
    def __init__(self, wiki, search, html, result):
        self.wiki = wiki
        self.html = html
        self.result = result
        self.exists = result != {}
        self.title = result.get('title', search)

    @property
    def content(self):
        if not self.exists:
            return {'':'Page Not Found.'}
        sections = parseExtract(self.html)
        sections.pop("External links", '')
        sections.pop("References", '')
        sections.pop("Contents", '')

        images = [self.wiki.articlepath.replace('$1', 'File:' + i)
                 for i in self.result['images']]
        #if an url starts with //, it can by http or https.  Use http.
        extlinks = ['http:' + i if i.startswith('//') else i
                for i in self.result['externallinks']]
        iwlinks = [i['url'] for i in self.result['iwlinks']]

        if images:
            sections['Images'] = '\n'.join(images) + '\n'
        if extlinks:
            sections['External links'] = '\n'.join(extlinks) + '\n'
        if iwlinks:
            sections['Interwiki links'] = '\n'.join(iwlinks) + '\n'
        return sections


class _Featured(object):
    exists = True

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
