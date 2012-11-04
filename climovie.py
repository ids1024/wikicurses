#! /usr/bin/env python

from __future__ import print_function
import urllib2
import json

API_KEY = "c5b633xj3ats73tmf9cez333"

base_url = "http://api.rottentomatoes.com/api/public/v1.0"


type = "/lists/movies/box_office.lson?apikey="


url = base_url + type + API_KEY

result = json.load(urllib2.urlopen(url))

k=0
z=0

for i in result["movies"]:
    print(i["title"])
    print("SYNOPSIS",end="\n")
    print(i["synopsis"],end="\n")
    print("TRAILER",end="\n")
    print(i["links"]["clips"],end="\n")
    print("CASTS",end="\n")
    for j in result["movies"][k]["abridged_cast"]:
        print(j["name"])
	print(j["characters"],end="\n\n\n")
    #for a in result["movies"]:
    print("CRITICS_RATING:",end="     ")
    print(result["movies"][z]["ratings"]["critics_rating"])
    print("CRITICS_SCORE:",end="      ")
    print(result["movies"][z]["ratings"]["critics_score"])
    print("AUDIENCE_RATING:",end="    ")
    print(result["movies"][z]["ratings"]["audience_rating"])
    print("AUDIENCE_SCORE:",end="     ")
    print(result["movies"][z]["ratings"]["audience_score"],end="\n\n\n")
    print("\t-----------------------------------------------------------")
    #print(i["abridged_cast"][j]["name"])
    #print(i["abridged_cast"][j]["characters"],end="\n\n\n") 
    z=z+1
    k=k+1
