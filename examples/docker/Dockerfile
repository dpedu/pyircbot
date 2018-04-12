FROM ubuntu:bionic

ENTRYPOINT ["/usr/local/bin/pyircbot"]
WORKDIR /srv/bot/
CMD ["-c", "config.json"]
ADD requirements.txt /tmp/requirements.txt

RUN apt-get update && \
    apt-get install -y python3 python3-setuptools python3-pip sqlite3 git && \
    pip3 install -r /tmp/requirements.txt && \
    useradd --home-dir /srv/bot bot && \
    chown bot /srv/bot && \
    apt-get remove -y python3-pip perl && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

COPY . /tmp/pyircbot/

RUN cd /tmp/pyircbot/ && \
    python3 setup.py install && \
    su -c "cp -r /tmp/pyircbot/examples/config.json /tmp/pyircbot/examples/data/ /srv/bot/" bot && \
    cd / && \
    rm -rf /tmp/pyircbot

USER bot
