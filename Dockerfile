FROM python:3.10-slim
MAINTAINER ecoron

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get -y install git wget curl sudo unzip openjdk-11-jre-headless xvfb libxi6 libgconf-2-4 gnupg && \
    apt-get autoremove -y && \
    apt-get autoclean -y

WORKDIR /serpscrap
COPY scripts/install_chrome.sh ./install_chrome.sh
RUN sh ./install_chrome.sh

COPY . .
RUN pip install --upgrade pip && pip install pipenv && pipenv install --deploy --system

# ENTRYPOINT ["python"]
