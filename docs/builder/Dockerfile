FROM ubuntu:trusty

COPY start /start

RUN apt-get update ; apt-get install -y python3 python3-dev python3-pip python3-yaml make wget python3-sphinx python3-setuptools unzip libmysqlclient-dev ; cd /tmp ; wget https://github.com/jgarzik/python-bitcoinrpc/archive/master.zip ; unzip master.zip ;  cd python-bitcoinrpc-master/ ; python3 setup.py install ; cd /tmp ; wget https://github.com/dpedu/MySQL-for-Python-3/archive/master.zip -O mysqldb.zip ; unzip mysqldb.zip ; cd MySQL-for-Python-3-master/ ; python3 setup.py install ; chmod +x /start ; mkdir /tmp/docs

VOLUME /tmp/docs

CMD ["/start"]
