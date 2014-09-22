import pkgutil

_data = pkgutil.get_data('wikicurses', 'interwiki.list').decode()
wikis = dict([i.split('|')[0:2] for i in _data.splitlines() if i[0]!='#'])

ITALIC, BOLD, BLOCKQUOTE = (1<<i for i in range(3))
