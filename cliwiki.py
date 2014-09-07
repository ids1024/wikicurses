#! /usr/bin/env python3

""" CLI to access wikipedia informations """

import sys
import os
import json
import urllib.request
import re
import argparse
import textwrap

from collections import OrderedDict
from subprocess import Popen, PIPE
from html.parser import HTMLParser


# **** Global Variables ****
BASE_URL = "http://en.wikipedia.org/w/api.php?"
TITLES = ""
RESULT = None
PAGE = None
PAGER = None


# **** Functions ****
class ExcerptHTMLParser(HTMLParser):
    sections = OrderedDict({'':''})
    cursection = ''
    inh2 = False
    inblockquote = False

    def add_text(self, text):
        if self.inh2:
            self.cursection += text
        elif self.inblockquote:
            self.sections[self.cursection] += '> ' + text
        else:
            self.sections[self.cursection] += text

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.inh2 = True
            self.cursection = ''
        elif re.fullmatch("h[3-6]", tag):
            self.add_text('\033[32m')
            num = int(re.sub("h([3-6])", "\\1", tag))
            self.add_text('\n'+'#'*num)
        elif tag == 'i':
            self.add_text('\033[3m')
        elif tag == 'b':
            self.add_text('\033[1m')
        elif tag == 'li':
            self.add_text("- ")
        elif tag == 'blockquote':
            self.inblockquote = True
        else:
            pass

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.inh2 = False
            self.sections[self.cursection] = ''
        elif re.fullmatch("h[3-6]", tag):
            self.add_text('\033[0m')
            self.add_text('\n')
        elif tag == 'i':
            self.add_text('\033[23m')
        elif tag == 'b':
            self.add_text('\033[21m')
        elif tag == 'p':
            self.add_text('\n')
        elif tag == 'blockquote':
            self.inblockquote = False
        else:
            pass

    def handle_data(self, data):
        text = data.replace('*', '\\*')
        text = re.sub('\n+', '\n', text)
        self.add_text(text)

def wiki_query():
    global RESULT
    global PAGE
    data = {"action":"query", "prop":"extracts|info|extlinks|images",
            "titles":TITLES, "redirects":True, "format":"json",
            "inprop":"url|displaytitle"}

    url = BASE_URL + urllib.parse.urlencode(data)
    # open url, read content (bytes), convert in string via decode()
    RESULT = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
    # In python 3 dict_keys are not indexable, so we need to use list()
    key = list(RESULT['query']['pages'])[0][:]
    PAGE = RESULT['query']['pages'][key]


def output(text):
    if PAGER is not None:
        print(text, file=PAGER.stdin)
    else:
        print(text)


def wiki_search():
    """ Search function """

    try:
        parser = ExcerptHTMLParser()
        parser.feed(PAGE['extract'])
        parser.sections.pop("External links", '')
        parser.sections.pop("References", '')

        wrapper = textwrap.TextWrapper(replace_whitespace=False,
                  drop_whitespace=False)
        for i in parser.sections:
            if i:
                output(i)
                output(len(i)*'-')
            for line in parser.sections[i].splitlines():
                output(wrapper.fill(line))



    except KeyError:
        output('No wikipedia page for that title. '
              'Wikipedia search titles are case sensitive.')



def url_and_displaytitle():
    """ Display URL and Title for the page """

    output(PAGE['title'])
    output(len(PAGE['title'])*'=')
    output('<'+PAGE['fullurl']+'>\n')



def interesting_links():
    """Fonction displaying related links => Interest on the CLI ?"""

    output('\nExternal Links')
    output(len('External Links')*'-'+'\n')

    try:
        offset = RESULT['query-continue']['extlinks']['eloffset']

        for j in range(0, offset):
            # ['*'] => elements of ....[j] are dict, and their keys are '*'
            link = PAGE['extlinks'][j]['*']
            if link.startswith("//"):
                link = "http:" + link
            output('- <'+link+'>')

    except KeyError:
        output("Sorry, we couldn't find any links.")



def images():
    """ Get images urls """

    image_url = "http://en.wikipedia.org/wiki/"

    output('\nImages')
    output(len('Images')*'-'+'\n')

    try:
        for i in range(1, len(PAGE['images'])):
            image = PAGE['images'][i]['title']
            image = image_url + image.replace(' ', '_')
            output('- <'+image+'>')

    except KeyError:
        pass


def featured_feed(feed):
    """Featured Feed"""

    data = {"action":"featuredfeed", "feed":feed, "format": "json"}
    url = BASE_URL + urllib.parse.urlencode(data)

    result = urllib.request.urlopen(url).read().decode('utf-8')

    re_title = re.compile('<title>(.*)</title>')
    re_links = re.compile('<link>(.*)en</link>')

    result1 = re.findall(re_title, result)
    result2 = re.findall(re_links, result)

    output('\n')

    for desc, url in zip(result1, result2):
        output(desc + ':\t ' + url)


def interwiki_links():
    """ Inter wiki links """

    output('Inter wiki links found for this search: ')

    url = BASE_URL + ACTION + TITLES + REDIRECTS + "&prop=iwlinks"+ FORMAT

    output(url)

    # TODO: parse the json, match it with a dict containing
    # url to append depending on the key returned in the url,
    # and then only show the resulting urls

    # result = urllib.request.urlopen(url).read().decode('utf-8')

    # for i in reslut:
        # print(i)


def main():
    """ Main function """

    # Gestion des paramètres
    parser = argparse.ArgumentParser(description =
                                        "Access Wikipedia from Command Line")

    parser.add_argument('--nopager',
                        action = 'store_true',
                        help="Do not display using a pager")

    group = parser.add_mutually_exclusive_group(required = True)

    group.add_argument('search',
                        nargs = '?',
                        default = '',
                        help = "Page to search for on Wikipedia")

    group.add_argument('-d', '--today',
                        action = 'store_const',
                        const = 'onthisday',
                        help='Display URLs for the "On this day" pages')

    group.add_argument('-f', '--featured',
                        action = 'store_const',
                        const = 'featured',
                        help = 'Display the featured articles URLs')

    group.add_argument('-p', '--picture',
                        action = 'store_const',
                        const = 'potd',
                        help='Display URLs for the "Picture of the day" pages')


    args = parser.parse_args()

    global PAGER
    if sys.stdout.isatty() and not args.nopager:
        pager = os.environ.get("PAGER", "less")
        if pager == "vimpager":
            pager = ("vimpager", "-c", "setf markdown")
        PAGER = Popen(pager, stdin=PIPE, universal_newlines=True)


    try:
        if args.search :
            global TITLES
            TITLES = args.search

            wiki_query()
            url_and_displaytitle()
            wiki_search()
            images()
            interesting_links()
            # interwiki_links()

        elif args.featured:
            featured_feed(args.featured)

        elif args.picture:
            featured_feed(args.picture)

        elif args.today:
            featured_feed(args.today)

        if PAGER is not None:
            PAGER.stdin.close()
            PAGER.wait()

    except KeyboardInterrupt:
        print('\n\n Program interrupted')


if __name__ == "__main__":
    main()
