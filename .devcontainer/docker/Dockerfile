FROM oraclelinux:9
CMD bash -c "/bin/bash"

LABEL maintainer=masahiro
RUN dnf -y install jq git make tar gzip wget glibc-langpack-ja

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

RUN dnf -y install python3-devel python3-pip python3-setuptools python3-pip-wheel
RUN pip3 install matplotlib pandas polars Flask polars django
RUN python3 -m pip install django-filter
RUN pip install djangorestframework