#! /usr/bin/env python3

""" CLI to access wikipedia informations """

import json
import urllib.request
import re
import argparse


# **** Global Variables ****
BASE_URL = "http://en.wikipedia.org/w/api.php?"
ACTION = "action=query"
FORMAT = "&format=json"
TITLES = "&titles="
REDIRECTS = "&redirects"



# **** Functions ****
def wiki_query(properties):
    url = (BASE_URL + ACTION + TITLES + REDIRECTS + properties + FORMAT)
    # open url, read content (bytes), convert in string via decode()
    return json.loads(urllib.request.urlopen(url).read().decode('utf-8'))



def wiki_search():
    """ Search function """

    prop = "&prop=extracts"
    plaintext = "&explaintext"
    section_format = "&exsectionformat=plain"

    try:
        result = wiki_query(prop + plaintext + section_format)

        key = list(result['query']['pages'].keys())[0][0:]

        print(result['query']['pages'][key]['extract'])

    except KeyError:
        print('No wikipedia page for that title. '
              'Wikipedia search titles are case sensitive.')



def url_and_displaytitle():

    """ Display URL and Title for the page """

    print('\n\nTitle and url for this Wikipedia page: \n')

    prop_inprop = "&prop=info&inprop=url|displaytitle"

    result = wiki_query(prop_inprop)

    # In python 3 dict_keys are not indexable, so we need to use list()
    key = list(result['query']['pages'].keys())[0][:]

    print('\t'+result['query']['pages'][key]['title'])
    print('\t'+result['query']['pages'][key]['fullurl'])
    print('\n\t-------------------\t')



def interesting_links():

    """Fonction displaying related links => Interest on the CLI ?"""

    print('\nYou may also be interested in the following links: \n')

    prop = "&prop=extlinks"

    try:
        result = wiki_query(prop)

        key = list(result['query']['pages'].keys())[0][0:]

        offset = result['query-continue']['extlinks']['eloffset']

        for j in range(0, offset):

            # ['*'] => elements of ....[j] are dict, and their keys are '*'
            print('\t'+result['query']['pages'][key]['extlinks'][j]['*'])

    except KeyError:
        print("Sorry, we couldn't find any links.")



def images():
    """ Get images urls """

    image_url = "http://en.wikipedia.org/wiki/"
    prop = "&prop=images"

    result = wiki_query(prop)

    print('\nAll images related to this search : \n')


    key = list(result['query']['pages'].keys())[0][0:]

    try:
        for i in range(1, len(result['query']['pages'][key]['images'])):

            image = result['query']['pages'][key]['images'][i]['title']
            image = image_url + image.replace(' ', '_')
            print('\t'+image)

        print('\n\t------------------\t')

    except KeyError:
        print('\n\t------------------\t')




def featured_feed(feed):
    """Featured Feed"""

    result = wiki_query("&action=featuredfeed" + "&feed=")

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
            TITLES += args.search.replace(' ','_')

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
