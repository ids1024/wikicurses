Wikicurses
==========

A simple curses interface for accessing Wikipedia.

This was originally a fork of [cliwiki](https://github.com/AnirudhBhat/cliWiki.py).

Usage
-----
~~~bash
$ wikicurses -h
usage: wikicurses [-h] [-d | -f | -p] [search]

A simple curses interface for accessing Wikipedia.

positional arguments:
  search          page to search for

optional arguments:
  -h, --help      show this help message and exit
  -d, --today     list "On This Day" pages
  -f, --featured  show featured articles
  -p, --picture   Show pictures of the day
~~~

Keybindings
-----------
o: Open searchbox

c: Open table of contents for page

^f or Page Down: scroll down a page

^b or Page Up: scroll up a page

j or Down: scroll down a line

k or Up: scoll up a line

q or :q(uit): exit

:bmark: add bookmark

:bmarks: view bookmarks
