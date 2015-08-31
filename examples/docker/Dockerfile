FROM ubuntu:trusty

RUN apt-get update ; \
    apt-get install -y python3 python3-setuptools python3-requests python3-yaml wget sqlite3 supervisor

RUN easy_install3 pip ; \
    pip3 install praw pytz ; \
    useradd bot ; \
    cd /tmp ; \
    wget http://gitlab.xmopx.net/dave/pyircbot3/repository/archive.tar.gz ; \
    tar zxvf archive.tar.gz ; \
    rm archive.tar.gz ;\
    cd pyircbot3.git/ ; \
    python3 setup.py install ; \
    mkdir /srv/bot ; \
    chown bot /srv/bot ; \
    echo "[supervisord]" >  /etc/supervisor/conf.d/supervisor.conf ; \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisor.conf ; \
    su -c "cp -r /tmp/pyircbot3.git/examples/config.json /tmp/pyircbot3.git/examples/data/ /srv/bot/" bot

ADD pyircbot.conf /etc/supervisor/conf.d/pyircbot.conf

CMD ["supervisord"]
