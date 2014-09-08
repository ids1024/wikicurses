import pkgutil

data = pkgutil.get_data('wikicurses', 'interwiki.list').decode()
wikis = dict([i.split('|')[0:2] for i in data.splitlines() if i[0]!='#'])
