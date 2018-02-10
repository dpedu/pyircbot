FROM ubuntu:artful

ADD ./ /tmp/pyircbot/

RUN apt-get update ; \
    apt-get install -y python3 python3-sphinx python3-setuptools python3-dev python3-pip make wget unzip git

RUN cd /tmp/pyircbot/ && pip3 install -r requirements.txt

COPY docs/builder/start /start

RUN chmod +x /start ; \
    mkdir /tmp/docs

ENTRYPOINT ["/start"]
