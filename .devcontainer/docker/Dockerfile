FROM oraclelinux:9
CMD bash -c "/bin/bash"

LABEL maintainer=masahiro

ARG UID=20000
ARG GID=20000

RUN groupadd -g $GID masahiro \
    && useradd -m -u $UID -g $GID masahiro

RUN dnf -y install jq git make tar gzip wget glibc-langpack-ja curl
RUN dnf install gettext

RUN echo 'root:P@ssw0rd' |chpasswd
RUN echo 'masahiro:P@ssw0rd' |chpasswd
RUN echo "masahiro    ALL=(ALL)       ALL" >> /etc/sudoers

RUN yum -y update && yum clean all

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

COPY requirements.txt /

RUN dnf -y install python3.12 python3.12-devel python3.12-pip python3.12-setuptools python3.12-pip-wheel
RUN rm /usr/bin/python3
RUN ln -s /usr/bin/python3.12 /usr/bin/python3
RUN python3.12 -m pip install -r /requirements.txt

RUN curl -fsSL https://rpm.nodesource.com/setup_22.x | bash -
RUN dnf install nodejs
RUN npm install -g yarn
RUN npm install -g typescript

USER masahiro