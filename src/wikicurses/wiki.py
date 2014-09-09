import json
import urllib.request
import re

from wikicurses.htmlparse import ExcerptHTMLParser
from wikicurses import wikis

class Wiki(object):
    result = None
    page = None

    def __init__(self, url):
        self.siteurl = url

    def search(self, titles):
        data = {"action":"query", "prop":"extracts|info|extlinks|images|iwlinks",
                "titles":titles, "redirects":True, "format":"json",
                "inprop":"url|displaytitle"}

        url = self.siteurl + urllib.parse.urlencode(data)
        # open url, read content (bytes), convert in string via decode()
        self.result = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
        # In python 3 dict_keys are not indexable, so we need to use list()
        key = list(self.result['query']['pages'])[0][:]
        self.page = self.result['query']['pages'][key]

    @property
    def title(self):
        return self.page['title']

    def __get_extract(self):
        """ Get extract """
        try:
            parser = ExcerptHTMLParser()
            parser.feed(self.page['extract'])
            parser.sections.pop("External links", '')
            parser.sections.pop("References", '')
            return parser.sections

        except KeyError:
            return {'':'No wikipedia page for that title.\n'
                   'Wikipedia search titles are case sensitive.'}

    def __get_external_links(self):
        """ Get external links """
        try:
            offset = self.result['query-continue']['extlinks']['eloffset']
            output = ''
            for j in range(0, offset):
                # ['*'] => elements of ....[j] are dict, and their keys are '*'
                link = self.page['extlinks'][j]['*']
                if link.startswith("//"):
                    link = "http:" + link
                output += link + '\n'
            return output
        except KeyError:
            pass

    def __get_interwiki_links(self):
        """ Inter wiki links """
        try:
            iwlinks = self.page['iwlinks']
        except KeyError:
            return
        output = ''
        for j in self.page['iwlinks']:
            try:
                output += wikis[j['prefix']].replace('$1', j['*']) + '\n'
            except KeyError:
                continue
        return output

    def __get_images(self):
        """ Get images urls """

        image_url = "http://en.wikipedia.org/wiki/"

        try:
            output = ''
            for i in range(1, len(self.page['images'])):
                image = self.page['images'][i]['title']
                image = image_url + image.replace(' ', '_')
                output += image + '\n'
            return output
        except KeyError:
            pass

    def get_content(self):
        sections = self.__get_extract()
        sections.update({
            'Images\n':self.__get_images(),
            '\nExternal links\n':self.__get_external_links(),
            '\nInterwiki links\n':self.__get_interwiki_links()
            })
        return sections

    def get_featured_feed(self, feed):
        """Featured Feed"""

        data = {"action":"featuredfeed", "feed":feed, "format": "json"}
        url = self.siteurl + urllib.parse.urlencode(data)

        result = urllib.request.urlopen(url).read().decode('utf-8')

        re_title = re.compile('<title>(.*)</title>')
        re_links = re.compile('<link>(.*)en</link>')

        result1 = re.findall(re_title, result)
        result2 = re.findall(re_links, result)

        output = '\n'
        for desc, url in zip(result1, result2):
            output += desc + ':\t ' + url
        return output
