#!/usr/bin/env python3

from distutils.core import setup

setup(name='Wikicurses',
      version='0.1',
      description='A simple curses interface for accessing Wikipedia.',
      author='Ian D. Scott',
      author_email='ian@perebruin.com',
    license = "MIT",
      url='http://github.com/ids1024/wikicurses/',
      packages = ['wikicurses'],
      package_dir={'wikicurses': 'src/wikicurses'},
      package_data={'wikicurses': ['interwiki.list']},
      scripts = ['wikicurses'],
     )
