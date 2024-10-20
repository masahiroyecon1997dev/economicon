FROM oraclelinux:9
CMD bash -c "/bin/bash"

LABEL maintainer=masahiro

ARG UID=20000
ARG GID=20000

RUN groupadd -g $GID masahiro \
    && useradd -m -u $UID -g $GID masahiro

RUN dnf -y install jq git make tar gzip wget glibc-langpack-ja curl

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

RUN dnf -y install python3.11 python3.11-devel python3.11-pip python3.11-setuptools python3.11-pip-wheel
RUN rm /usr/bin/python3
RUN ln -s /usr/bin/python3.11 /usr/bin/python3
RUN python3.11 -m pip install matplotlib pandas polars Flask polars django django-filter djangorestframework django-cors-headers

RUN curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
RUN dnf install nodejs
RUN npm install -g yarn
RUN npm install -g typescript

USER masahiro