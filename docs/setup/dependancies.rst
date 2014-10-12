************
Dependancies
************

PyIRCBot is designed to run on Python 3, and is usually tested with 3.4. Several
modules are needed that are available for both version of python.

The following non-core Python modules are needed, and easily available through
Pip for python 3:

 - praw
 - pytz
 - PyYAML (yaml)
 - requests
 
The following modules aren't available on pip, and are sourced from various
places. They are NOT required but certain modules won't be available without
them.

 - **bitcoinrpc** - https://github.com/jgarzik/python-bitcoinrpc
 - **pymysql** - https://github.com/dpedu/MySQL-for-Python-3 (needs \
   libmysqlclient-dev on your system)
