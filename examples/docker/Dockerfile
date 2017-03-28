FROM ubuntu:xenial

ENTRYPOINT ["/usr/local/bin/pyircbot"]
WORKDIR /srv/bot/
CMD ["-c", "config.json"]

RUN useradd bot ; \
    sed -i -e 's/archive.ubuntu.com/mirrors.digitalocean.com/' /etc/apt/sources.list ; \
    apt-get update ; \
    apt-get install -y python3 python3-setuptools python3-requests curl unzip sqlite3 ; \
    easy_install3 pip ; \
    pip3 install praw pytz ; \
    curl -o /tmp/bitcoinrpc.zip https://codeload.github.com/dpedu/python-bitcoinrpc/zip/master ; \
    unzip bitcoinrpc.zip ; \
    cd python-bitcoinrpc-master ; \
    python3 setup.py install ; \
    useradd bot ; \
    mkdir /srv/bot ; \
    chown bot /srv/bot ; \
    rm -rf /var/lib/apt/lists/* /tmp/bitcoinrpc.zip /tmp/python-bitcoinrpc-master

COPY . /tmp/pyircbot/

RUN cd /tmp/pyircbot/ ; \
    python3 setup.py install ; \
    su -c "cp -r /tmp/pyircbot/examples/config.json /tmp/pyircbot/examples/data/ /srv/bot/" bot ; \
    cd / ; \
    rm -rf /tmp/pyircbot

USER bot
