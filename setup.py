#!/usr/bin/env python3

from distutils.core import setup

setup(name='Wikicurses',
      version='1.1',
      description='A simple curses interface for accessing Wikipedia.',
      author='Ian D. Scott',
      author_email='ian@perebruin.com',
      license = "MIT",
      url='http://github.com/ids1024/wikicurses/',
      packages = ['wikicurses'],
      package_dir={'wikicurses': 'src/wikicurses'},
      data_files=[
          ('/etc', ['wikicurses.conf']),
          ('/usr/share/man/man1', ['wikicurses.1']),
          ('/usr/share/man/man5', ['wikicurses.conf.5']),
          ('/usr/share/zsh/site-functions', ['_wikicurses'])
          ],
      scripts = ['wikicurses'],
     )
