FROM ecoron/python36-sklearn
MAINTAINER ecoron

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get -y install git wget curl sudo
RUN apt-get autoremove
RUN apt-get autoclean

RUN mkdir serpscrap
COPY install_chrome.sh .install_chrome.sh
RUN sh .install_chrome.sh

RUN pip install SerpScrap

# ENTRYPOINT python
