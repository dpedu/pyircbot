FROM ubuntu:xenial

RUN apt-get update ; \
    apt-get install -y python3 python3-sphinx python3-setuptools python3-dev python3-requests python3-pip python3-lxml make wget unzip libmysqlclient-dev

RUN pip3 install pytz praw

RUN cd /tmp ; \
    wget https://github.com/jgarzik/python-bitcoinrpc/archive/master.zip ; \
    unzip master.zip ; \
    cd python-bitcoinrpc-master/ ; \
    python3 setup.py install

RUN cd /tmp ; \
    wget https://github.com/dpedu/MySQL-for-Python-3/archive/master.zip -O mysqldb.zip ; \
    unzip mysqldb.zip ; \
    cd MySQL-for-Python-3-master/ ; \
    python3 setup.py install

COPY start /start

RUN chmod +x /start ; \
    mkdir /tmp/docs

ENTRYPOINT ["/start"]
