#! /usr/bin/env python3

""" CLI to access wikipedia informations """

import json
import urllib.request
import sys
import re
# import argparse


# **** Global Variables ****
BASE_URL = "http://en.wikipedia.org/w/api.php?"
ACTION = "action=query"
FORMAT = "&format=json"
TITLES = "&titles="



# **** Functions ****

def get_title():
    """ Ask the user for a title and store the input """

    title = input('Enter the title you want to search --> \n')
    global TITLES
    TITLES += title.replace(' ','_')



def wiki_search():
    """ Search function """

    prop = "&prop=extracts"
    plaintext = "&explaintext"
    section_format = "&exsectionformat=plain"

    try:
        url = (BASE_URL + ACTION + TITLES
            + prop + plaintext + section_format + FORMAT)

        # open url, read content (bytes), convert in string via decode()
        result = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

        key = list(result['query']['pages'].keys())[0][0:]

        print(result['query']['pages'][key]['extract'])

    except KeyError:
        print('No wikipedia page for that title. '
              'Wikipedia search titles are case sensitive.')



def url_and_displaytitle():

    """ Display URL and Title for the page """

    print('\n\nTitle and url for this Wikipedia page: \n')

    prop_inprop = "&prop=info&inprop=url|displaytitle"

    url = BASE_URL + ACTION + TITLES + prop_inprop + FORMAT

    # open url, read content (bytes), convert in string via decode()
    result = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

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
        url = BASE_URL + ACTION + TITLES + prop + FORMAT

        # open url, read content (bytes), convert in string via decode()
        result = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

        key = list(result['query']['pages'].keys())[0][0:]

        offset = result['query-continue']['extlinks']['eloffset']

        for j in range(0, offset):

            # ['*'] => elements of ....[j] are dict, and their keys are '*'
            print('\t'+result['query']['pages'][key]['extlinks'][j]['*'])

    except KeyError:
        print("Sorry, we couldn't find any links.")



def images():
    """ Get images urls """

    print('\nAll images related to this search : \n')
    image_url = "http://en.wikipedia.org/wiki/"

    prop = "&prop=images"

    url = BASE_URL + ACTION + TITLES + prop + FORMAT

    # open url, read content (bytes), convert in string via decode()
    result = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))

    key = list(result['query']['pages'].keys())[0][0:]

    try:
        for i in range(1, len(result['query']['pages'][key]['images'])):

            image = result['query']['pages'][key]['images'][i]['title']
            image = image_url + image.replace(' ','_')
            print('\t'+image)

        print('\n\t------------------\t')

    except KeyError:
        print('\n\t------------------\t')




def featured_feed():
    """Featured Feed"""

    ACTION = "&action=featuredfeed"

    feed = "&feed=" + sys.argv[1]
    url = BASE_URL + ACTION + feed + FORMAT

    print(url)

    result = urllib.request.urlopen(url).read().decode('utf-8')

    res1 = re.compile('<title>(.*)</title>')
    res2 = re.compile('<link>(.*)en</link>')

    result1 = re.findall(res1, result)
    result2 = re.findall(res2, result)

    for i in enumerate(zip(result1, result2)):
        print(i)



#def interwiki_links():
 #   print('inter wiki links found for this search',end="\n")
  #  BASE_URL
   # ACTION
   #  TITLES
  #  prop = "&prop=iwlinks"
  #  url = BASE_URL + ACTION + TITLES + prop
  #  print(url)
  #  result = urllib2.urlopen(url)
  #  for i in result:
  #      print(i)



def main():
    """ Main function """
    if len(sys.argv) < 2:
        get_title()
        wiki_search()
        url_and_displaytitle()
        images()
        #interwiki_links()
        interesting_links()
    else:
        featured_feed()



if __name__ == "__main__":
    main()
