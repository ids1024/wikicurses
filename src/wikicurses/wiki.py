import json
import urllib.request
import http.cookiejar
import time
import hashlib
import sys
from bs4 import BeautifulSoup
from collections import OrderedDict
from functools import lru_cache
from wikicurses.htmlparse import parseExtract, parseFeature
from wikicurses.settings import Settings, wikis, conf

useragent = "Wikicurses/1.1 (https://github.com/ids1024/wikicurses)"\
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

    @classmethod
    def fromName(cls, name):
        url = conf[name]['url']
        username = conf[name].get('username')
        password = conf[name].get('password')
        return cls(url, username, password)

    @classmethod
    def fromApiUrl(cls, url):
        wikiname = {v: k for k, v in wikis().items()}.get(url)
        username = password = None
        if wikiname:
            username = conf[wikiname].get('username')
            password = conf[wikiname].get('password')
        return cls(url, username, password)

    @classmethod
    def fromPageUrl(cls, url):
        html = urllib.request.urlopen(url).read().decode()
        soup = BeautifulSoup(html, 'lxml')
        link = soup.find('link', rel='EditURI')
        if not link:
            return None
        rsdurl = urllib.parse.urljoin(url, link['href'])
        rsd = urllib.request.urlopen(rsdurl).read().decode()
        soup = BeautifulSoup(rsd, "xml")
        apiurl = soup.find('api', {'name': 'MediaWiki'})['apiLink']
        return cls.fromApiUrl(apiurl)

    @lru_cache(1)
    def get_siteinfo(self):
        result = self._query(action="query", meta="siteinfo",
                             siprop="general", format="json")
        query = json.loads(result)["query"]
        self.articlepath = urllib.parse.urljoin(
            query['general']['base'],
            query['general']['articlepath'])
        self.mainpage = query['general']['mainpage']

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
        return rev['*'], (rev['timestamp'], starttime)

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
        if result['result'] != 'Success':
            raise WikiError(result['result'])

    @lru_cache(16)
    def search(self, name):
        """Search wiki for article and return _Article object."""
        self.get_siteinfo()
        if not name:
            name = self.mainpage
        result = json.loads(self._query(action="parse", page=name,
                                        prop="images|externallinks|iwlinks|"
                                        "links|displaytitle|properties|text",
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
        return _Featured(feed, BeautifulSoup(result, "xml").find("channel"))

    @lru_cache(16)
    def search_sugestions(self, name):
        """Return list of search suggestions for specified string."""
        result = self._query(action="opensearch", search=name, format="json")
        return json.loads(result)[1]

    def random(self):
        """Return the name of a random page."""
        result = json.loads(self._query(action="query", list="random",
            rnnamespace=0, format="json"))
        return result["query"]["random"][0]["title"]

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
    links = []
    iwlinks = []

    def __init__(self, wiki, search, result):
        self.wiki = wiki
        self.title = result.get('title', search)
        self.result = result
        self.exists = result != {}
        if self.exists:
            self.properties = {i['name']: i['*'] for i in result['properties']}
            self.html = result['text']['*']
            self.links = [i['*'] for i in result['links'] if ('exists' in i)
                    and not any(i['*'].startswith(j + ':') for j in
                        ('Category', 'Template', 'Template talk', 'Wikipedia'))]
            self.iwlinks = [(i['*'].split(':', 1)[1], i['url'])
                            for i in self.result['iwlinks']]

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

        if images:
            sections['Images'] = '\n'.join(images) + '\n'
        if extlinks:
            sections['External links'] = '\n'.join(extlinks) + '\n'
        return sections


class _Featured(object):
    exists = True
    properties = {}
    links = []
    iwlinks = []

    def __init__(self, feed, result):
        self.feed = feed
        self.result = result
        self.title = result.find('title').text
        self.content = OrderedDict()
        for i in self.result.find_all('item'):
            description = i.find('description').text
            text = parseFeature(description)
            self.content[i.find('title').text] = i.find(
                'link').text + '\n' + text


cookiejar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookiejar))
opener.addheaders = [('User-agent', useragent)]
urllib.request.install_opener(opener)
