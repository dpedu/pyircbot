FROM ubuntu:bionic

RUN apt-get update && \
    apt-get install -y python3-pip git && \
    useradd --home-dir /srv/bot bot && \
    mkdir -p /srv/bot && \
    chown bot /srv/bot

COPY ./requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

COPY ./ /tmp/pyircbot
RUN cd /tmp/pyircbot && \
    python3 setup.py install

ENTRYPOINT ["/usr/local/bin/pyircbot"]
WORKDIR /srv/bot/
CMD ["-c", "config.json"]
USER bot

