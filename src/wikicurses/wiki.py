import json
import urllib.request
import http.cookiejar
import time
import hashlib
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from functools import lru_cache
from wikicurses.htmlparse import parseExtract, parseFeature
from wikicurses.settings import Settings

useragent = "Wikicurses/0.1 (https://github.com/ids1024/wikicurses)"\
            " Python-urllib/%d.%d" % sys.version_info[:2]


class WikiError(Exception):
    pass


class Wiki(object):
    """A mediawiki wiki."""
    csrftoken = None

    def __init__(self, url, username, password):
        self.siteurl = url
        self.username = username
        self.password = password
        self.bmarks = Settings(url, 'bookmarks')

    @lru_cache(1)
    def get_siteinfo(self):
        result = self._query(action="query", meta="siteinfo",
                             siprop="general", format="json")
        query = json.loads(result)["query"]
        self.articlepath = urllib.parse.urljoin(
            query['general']['base'],
            query['general']['articlepath'])

    def _query(self, post=False, **kwargs):
        params = {k: v for k, v in kwargs.items() if v is not False}
        data = urllib.parse.urlencode(params)
        url = self.siteurl
        if post:
            data = data.encode()
        if not post:
            url += '?' + data
            data = None
        return urllib.request.urlopen(url, data).read().decode('utf-8')

    def login(self):
        """Log in to wiki using stored credentials."""
        if self.csrftoken:  # Already logged in
            return
        query = {'post': True, 'action': 'login', 'format': 'json',
                 'lgname': self.username, 'lgpassword': self.password}
        result = json.loads(self._query(**query))['login']
        if result['result'] == 'NeedToken':
            result = json.loads(
                self._query(lgtoken=result['token'], **query))['login']
        if result['result'] != 'Success':  # Error
            raise WikiError(result['result'])
        self.csrftoken = json.loads(self._query(post=True, action='query',
                                                meta='tokens', format='json')
                                    )['query']['tokens']['csrftoken']

    def logout(self):
        """Log out of wiki."""
        self._query(action='logout', format='json')
        self.csrftoken = None

    def init_edit(self, title):
        """Initialize edit of page.

        Return tuple (text, verify) where text is the text to be modified and
        verify should be passed to commit_edit().
        """
        result = json.loads(self._query(action='query', prop='revisions',
                                        rvprop='timestamp|content',
                                        titles=title, format='json'))['query']
        if "missing" in result:
            raise WikiError("Page Not Found")

        rev = next(iter(result['pages'].values()))['revisions'][0]
        starttime = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        return (rev['*'], (rev['timestamp'], starttime))

    def commit_edit(self, title, text, summary, minor, verify):
        """Commit edit of page.
        
        Required arguments:
        title -- the name of the page to be modified
        text -- the new text to be saved
        summary -- edit summary
        minor -- boolean value; True if edit is minor
        verify -- the verification tuple returned by init_edit()
        """
        md5sum = hashlib.md5(text.encode()).hexdigest()
        result = json.loads(self._query(post=True, action='edit', text=text,
                                        title=title, basetimestamp=verify[0],
                                        starttimestamp=verify[1], md5=md5sum,
                                        token=self.csrftoken, summary=summary,
                                        minor=minor, format='json'))['edit']
        self.search.cache_clear()
        return result['result']

    @lru_cache(16)
    def search(self, name):
        """Search wiki for article and return _Article object."""
        self.get_siteinfo()
        result = json.loads(self._query(action="parse", page=name,
                                        prop="images|externallinks|iwlinks|"
                                        "displaytitle|properties|text",
                                        format="json", redirects=True
                                        )).get('parse', {})
        return _Article(self, name, result)

    @lru_cache(1)
    def list_featured_feeds(self):
        """Return a list of available featured feeds."""
        result = json.loads(self._query(action="paraminfo",
                                        modules="featuredfeed",
                                        format="json"))["paraminfo"]
        if not result["modules"]:
            return []
        return next(i for i in result["modules"][0]["parameters"]
                    if i["name"] == "feed")["type"]

    @lru_cache(16)
    def get_featured_feed(self, feed):
        result = self._query(action="featuredfeed", feed=feed)
        return _Featured(feed, ET.fromstring(result)[0])

    @lru_cache(16)
    def search_sugestions(self, name):
        """Return list of search suggestions for specified string."""
        result = self._query(action="opensearch", search=name, format="json")
        return json.loads(result)[1]

    def clear_cache(self):
        """Clear the cache."""
        self.get_siteinfo.cache_clear()
        self.search.cache_clear()
        self.list_featured_feeds.cache_clear()
        self.get_featured_feed.cache_clear()
        self.search_sugestions.cache_clear()


class _Article(object):
    properties = {}
    html = ''

    def __init__(self, wiki, search, result):
        self.wiki = wiki
        self.title = result.get('title', search)
        self.result = result
        self.exists = result != {}
        if self.exists:
            self.properties = {i['name']: i['*'] for i in result['properties']}
            self.html = result['text']['*']

    @property
    def content(self):
        if not self.exists:
            return {'': ['Page Not Found.']}
        sections = parseExtract(self.html)

        images = [self.wiki.articlepath.replace('$1', 'File:' + i)
                  for i in self.result['images']]
        # if an url starts with //, it can by http or https.  Use http.
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
            self.content[i.findtext('title')] = i.findtext(
                'link') + '\n' + text


cookiejar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookiejar))
opener.addheaders = [('User-agent', useragent)]
urllib.request.install_opener(opener)
