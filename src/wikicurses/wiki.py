import json
import urllib.request
import http.cookiejar
import re
import time
import hashlib
import sys
import  xml.etree.ElementTree as ET
from collections import OrderedDict
from functools import lru_cache
from wikicurses.htmlparse import parseExtract, parseFeature

useragent = "Wikicurses/0.1 (https://github.com/ids1024/wikicurses)"\
            " Python-urllib/%d.%d" % sys.version_info[0:2]

@lru_cache(16)
class Wiki(object):
    csrftoken = None

    def __init__(self, url, username, password):
        self.siteurl = url
        self.username = username
        self.password = password

    @lru_cache(1)
    def get_siteinfo(self):
        result = self._query(action="query", meta="siteinfo",
                siprop="extensions|general", format="json")
        query = json.loads(result)["query"]

        extensions = (i["name"] for i in query["extensions"])
        self.has_extract = "TextExtracts" in extensions
        self.articlepath = urllib.parse.urljoin( 
                query['general']['base'],
                query['general']['articlepath'])

    def _query(self, post=False, **kargs):
        params = kargs.copy()
        for name, value in kargs.items():
            if value is False:
                params.pop(name)
        data =  urllib.parse.urlencode(params)
        headers = {'User-Agent':useragent}
        if post:
            request = urllib.request.Request(self.siteurl, data.encode(), headers)
        else:
            request = urllib.request.Request(self.siteurl + '?' + data, None, headers)
        return urllib.request.urlopen(request).read().decode('utf-8')

    def login(self):
        result = json.loads(self._query(post=True, action='login',
                lgname=self.username, lgpassword=self.password,
                format='json'))['login']
        if result['result'] == 'NeedToken':
            result = json.loads(self._query(post=True, action='login',
                lgname=self.username, lgpassword=self.password,
                lgtoken=result['token'], format='json'))['login']

        if result['result'] != 'Success': #Error
            return result['result']
        self.csrftoken = json.loads(self._query(post=True, action='query',
            meta='tokens', format='json'))['query']['tokens']['csrftoken']

    def logout(self):
        self._query(action='logout', format='json')
        self.csrftoken = None

    def init_edit(self, title):
        result = json.loads(self._query(action='query', prop='revisions',
            rvprop='timestamp|content', titles=title, format='json'))['query']
        if "missing" in result:
            return

        rev = next(iter(result['pages'].values()))['revisions'][0]
        starttime = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        return (rev['*'], (rev['timestamp'], starttime))

    def commit_edit(self, title, text, summary, minor, verify):
        md5sum = hashlib.md5(text.encode()).hexdigest()
        result = json.loads(self._query(post=True, action='edit', text=text,
                title=title, basetimestamp=verify[0], starttimestamp=verify[1],
                md5=md5sum, token=self.csrftoken, summary=summary, minor=minor,
                format='json'))['edit']
        self.search.cache_clear()
        return result['result']

    @lru_cache(16)
    def search(self, name):
        self.get_siteinfo()
        html = ''

        result = json.loads(self._query(action="parse", page=name,
                 prop="images|externallinks|iwlinks|displaytitle|properties|text",
                 format="json", redirects=True,)).get('parse', {})

        if self.has_extract:
            exresult = json.loads(self._query(action="query", redirects=True,
                     titles=name, prop="extracts", format="json"))['query']
            html = next(iter(exresult['pages'].values())).get('extract', '')

        elif 'text' in result:
            html = result['text']['*']

        return _Article(self, name, html, result)

    @lru_cache(1)
    def list_featured_feeds(self):
         result = json.loads(self._query(action="paraminfo",
             modules="featuredfeed", format="json"))["paraminfo"]
         if not result["modules"]:
             return []
         return next(i for i in result["modules"][0]["parameters"]
                 if i["name"]=="feed")["type"]

    @lru_cache(16)
    def get_featured_feed(self, feed):
        result = self._query(action="featuredfeed", feed=feed)
        return _Featured(feed, ET.fromstring(result)[0])

    @lru_cache(16)
    def search_sugestions(self, name):
        result = self._query(action="opensearch", search=name, format="json")
        return json.loads(result)[1]


class _Article(object):
    properties = {}

    def __init__(self, wiki, search, html, result):
        self.wiki = wiki
        self.html = html
        self.result = result
        self.exists = result != {}
        self.title = result.get('title', search)
        if 'properties' in result:
            self.properties = {i['name']: i['*'] for i in result['properties']}

    @property
    def content(self):
        if not self.exists:
            return {'':'Page Not Found.'}
        sections = parseExtract(self.html)

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
    properties = {}

    def __init__(self, feed, result):
        self.feed = feed
        self.result = result
        self.title = result.find('title').text
        self.content = OrderedDict()
        for i in self.result.findall('item'):
            description = i.findtext('description')
            text = parseFeature(description)
            self.content[i.findtext('title')] = i.findtext('link') + '\n' + text

            
cookiejar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
urllib.request.install_opener(opener)
