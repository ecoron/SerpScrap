FROM debian:jessie-slim

MAINTAINER ecoron

RUN echo 'deb http://ftp.de.debian.org/debian jessie main' >> /etc/apt/sources.list
RUN echo 'deb http://security.debian.org/debian-security jessie/updates main ' >> /etc/apt/sources.list
RUN echo 'deb http://ftp.de.debian.org/debian sid main' >> /etc/apt/sources.list

RUN apt-get update

RUN apt-get -y install git
RUN apt-get -y install wget
RUN apt-get -y install python3.6

RUN wget https://bootstrap.pypa.io/get-pip.py

RUN python3.6 get-pip.py

RUN rm get-pip.py

RUN cd /usr/local/bin \
  && rm -f easy_install \
  && rm -f pip \
  && rm -f pydoc \
  && rm -f python

RUN cd /usr/local/bin \
  && ln -s easy_install-3.6 easy_install \
  && ln -s pip3.6 pip \
  && ln -s /usr/bin/pydoc3.6 pydoc \
  && ln -s /usr/bin/python3.6 python

RUN apt-get autoremove
RUN apt-get autoclean

RUN echo 'alias python=python3.6' >> ~/.bashrc

RUN pip install SerpScrap --process-dependency-links

CMD chcp 65001
CMD set PYTHONIOENCODING=utf-8

ENTRYPOINT python
