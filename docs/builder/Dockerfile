FROM ubuntu:bionic

RUN apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y python3 python3-sphinx python3-setuptools python3-dev python3-pip make wget unzip git

COPY ./docs/builder/start /start

COPY ./ /tmp/pyircbot/

RUN cd /tmp/pyircbot/ && pip3 install -r requirements-test.txt

RUN chmod +x /start ; \
    mkdir /tmp/docs

ENTRYPOINT ["/start"]
