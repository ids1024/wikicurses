#! /usr/bin/env python

from __future__ import print_function
import json
import urllib2
import sys
import re



KEY = 0

base_url = "http://en.wikipedia.org/w/api.php?"

action = "action=query"


Format = "&format=json"


titles="&titles="




def get_title():
    title = raw_input('enter the title you want to search\n')
    title = title.replace(' ','_')
    global titles
    titles = titles + title



def url_and_displaytitle():
    print('\ntitle and url for this wikipedia site',end="\n")
    global base_url
    global action
    global titles
    global Format
    prop = "&prop=info"
    inprop = "&inprop=url|displaytitle"
    url = base_url + action + titles + prop + inprop + Format
    result = json.load(urllib2.urlopen(url))  
    key = result['query']['pages'].keys()
    global KEY
    KEY = (key[0][:])
    print(result['query']['pages'][str(KEY)]['title'])
    print(result['query']['pages'][str(KEY)]['fullurl'])
    print('\t-------------------\t')
        


def interesting_links():
    print('\nyou may also be interested in the following links',end="\n") 
    global base_url
    global Format
    global action
    global titles
    prop = "&prop=extlinks"
    try:
        url = base_url + action + titles + prop + Format
        result =json.load(urllib2.urlopen(url))
        key = result['query']['pages'].keys()
        key = key[0][0:]
        j = 0
        offset = result['query-continue']['extlinks']['eloffset']
        while j < offset:
            print(result['query']['pages'][str(key)]['extlinks'][j])
            j=j+1
    except:
        print('sorry,couldn\'t find any links') 




#def interwiki_links():
 #   print('inter wiki links found for this search',end="\n")
  #  base_url
   # action
   #  titles
  #  prop = "&prop=iwlinks"
  #  url = base_url + action + titles + prop
  #  print(url)
  #  result = urllib2.urlopen(url)
  #  for i in result:
  #      print(i)




def wiki_search():
    global base_url
    global action
    global titles
    global Format
    prop = "&prop=extracts"
    plaintext = "&explaintext"
    section_format = "&exsectionformat=plain"
    try:
        url = base_url + action + titles + prop + plaintext + section_format + Format
        result = json.load(urllib2.urlopen(url))
        key = result['query']['pages'].keys()
        key = key[0][0:]
        print(result['query']['pages'][str(key)]['extract'],end="\n")
    except:
        print('oops!,no wikipedia page for that title.Wikipedia search titles are case Sensitive...')
    




def images():
    print('\nall images related to this search',end="\n")
    image_url = "http://en.wikipedia.org/wiki/"
    global base_url
    global Format
    global action
    global titles
    prop = "&prop=images"
    url = base_url + action + titles + prop + Format
    result = json.load(urllib2.urlopen(url))
    key = result['query']['pages'].keys()
    key = key[0][0:]
    try:
        i = 1
        while(i):
            Image = str(result['query']['pages'][str(key)]['images'][i]['title'])
            image = image_url + Image.replace(' ','_')
            print(image)
            i=i+1
    except:
        print('\t------------------\t',end="\n")
        pass     
    






def featured_feed():
    global base_url
    Format = "&format=json"
    action = "&action=featuredfeed"
    try:
        feed = "&feed=" + str(sys.argv[1])
        url = base_url + action + feed + Format
        print(url)
        result = urllib2.urlopen(url).read()
        res1 = re.compile('<title>(.*)</title>')
        res2 = re.compile('<link>(.*)en</link>')
        Result1 = re.findall(res1,result)
        Result2 = re.findall(res2,result)
        for i in enumerate(zip(Result1,Result2)):
            print(i)
    except:
        print('error!')

        
    





if len(sys.argv) < 2:
    get_title()
    wiki_search()
    url_and_displaytitle()
    images()
    #interwiki_links()
    interesting_links()
else:
    featured_feed()






