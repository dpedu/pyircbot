FROM ubuntu:trusty

RUN apt-get update ; \
    apt-get install -y python3 python3-setuptools python3-requests curl sqlite3 supervisor ; \
    easy_install3 pip ; \
    pip3 install praw pytz ; \
    useradd bot ; \
    cd /tmp ; \
    mkdir pyircbot3.git ; \
    curl http://gitlab.xmopx.net/dave/pyircbot3/repository/archive.tar.gz | tar zxvf - -C pyircbot3.git --strip-components=1 ; \
    cd pyircbot3.git/ ; \
    python3 setup.py install ; \
    mkdir /srv/bot ; \
    chown bot /srv/bot ; \
    echo "[supervisord]" >  /etc/supervisor/conf.d/supervisor.conf ; \
    echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisor.conf ; \
    su -c "cp -r /tmp/pyircbot3.git/examples/config.json /tmp/pyircbot3.git/examples/data/ /srv/bot/" bot ; \
    rm -rf /var/lib/apt/lists/*

ADD pyircbot.conf /etc/supervisor/conf.d/pyircbot.conf

CMD ["supervisord"]
