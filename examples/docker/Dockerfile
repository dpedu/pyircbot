FROM ubuntu:xenial

ENTRYPOINT ["/usr/local/bin/pyircbot"]
WORKDIR /srv/bot/
CMD ["-c", "config.json"]

RUN sed -i -e 's/archive.ubuntu.com/mirrors.digitalocean.com/' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y python3 python3-setuptools python3-requests curl unzip sqlite3 && \
    easy_install3 pip && \
    pip3 install praw==5.0.1 pytz && \
    cd /tmp && \
    curl -o bitcoinrpc.tar.gz https://codeload.github.com/dpedu/python-bitcoinrpc/tar.gz/master && \
    tar zxvf bitcoinrpc.tar.gz && \
    cd python-bitcoinrpc-master && \
    python3 setup.py install && \
    useradd --home-dir /srv/bot bot && \
    chown bot /srv/bot && \
    rm -rf /var/lib/apt/lists/* /tmp/bitcoinrpc.tar.gz /tmp/python-bitcoinrpc-master

COPY . /tmp/pyircbot/

RUN cd /tmp/pyircbot/ && \
    python3 setup.py install && \
    su -c "cp -r /tmp/pyircbot/examples/config.json /tmp/pyircbot/examples/data/ /srv/bot/" bot && \
    cd / && \
    rm -rf /tmp/pyircbot

USER bot
