#! /usr/bin/env python3

""" CLI to access wikipedia informations """

import json
import urllib.request
import re
import argparse


# **** Global Variables ****
BASE_URL = "http://en.wikipedia.org/w/api.php?"
TITLES = ""
RESULT = None
PAGE = None


# **** Functions ****
def wiki_query():
    global RESULT
    global PAGE
    data = {"action":"query", "prop":"extracts|info|extlinks|images",
            "titles":TITLES, "redirects":True, "format":"json",
            "explaintext":True, "exsectionformat":"plain",
            "inprop":"url|displaytitle"}
    url = BASE_URL + urllib.parse.urlencode(data)
    # open url, read content (bytes), convert in string via decode()
    RESULT = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
    # In python 3 dict_keys are not indexable, so we need to use list()
    key = list(RESULT['query']['pages'].keys())[0][:]
    PAGE = RESULT['query']['pages'][key]



def wiki_search():

    """ Search function """

    try:
        print(PAGE['extract'])

    except KeyError:
        print('No wikipedia page for that title. '
              'Wikipedia search titles are case sensitive.')



def url_and_displaytitle():

    """ Display URL and Title for the page """

    print('\n\nTitle and url for this Wikipedia page: \n')

    print('\t'+PAGE['title'])
    print('\t'+PAGE['fullurl'])
    print('\n\t-------------------\t')



def interesting_links():

    """Fonction displaying related links => Interest on the CLI ?"""

    print('\nYou may also be interested in the following links: \n')

    try:
        offset = RESULT['query-continue']['extlinks']['eloffset']

        for j in range(0, offset):

            # ['*'] => elements of ....[j] are dict, and their keys are '*'
            link = PAGE['extlinks'][j]['*']
            if link.startswith("//"):
                link = "http:" + link
            print('\t'+link)

    except KeyError:
        print("Sorry, we couldn't find any links.")



def images():
    """ Get images urls """

    image_url = "http://en.wikipedia.org/wiki/"

    print('\nAll images related to this search : \n')

    try:
        for i in range(1, len(PAGE['images'])):

            image = PAGE['images'][i]['title']
            image = image_url + image.replace(' ', '_')
            print('\t'+image)

        print('\n\t------------------\t')

    except KeyError:
        print('\n\t------------------\t')




def featured_feed(feed):
    """Featured Feed"""

    result = wiki_query(action="featuredfeed", feed="")

    re_title = re.compile('<title>(.*)</title>')
    re_links = re.compile('<link>(.*)en</link>')

    result1 = re.findall(re_title, result)
    result2 = re.findall(re_links, result)

    print('\n')

    for desc, url in zip(result1, result2):
        print(desc + ':\t ' + url)




def interwiki_links():
    """ Inter wiki links """

    print('Inter wiki links found for this search: ')

    url = BASE_URL + ACTION + TITLES + REDIRECTS + "&prop=iwlinks"+ FORMAT

    print(url)

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

    parser.add_argument('search', help = "Page to search for on Wikipedia")

    group = parser.add_mutually_exclusive_group()

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

    try:
        if args.search :

            global TITLES
            TITLES = args.search

            wiki_query()
            wiki_search()
            url_and_displaytitle()
            images()
            interesting_links()
            # interwiki_links()

        elif args.featured:
            featured_feed(args.featured)

        elif args.picture:
            featured_feed(args.picture)

        elif args.today:
            featured_feed(args.today)

    except KeyboardInterrupt:
        print('\n\n Program interrupted')



if __name__ == "__main__":
    main()
