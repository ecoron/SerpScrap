FROM ecoron/python36-sklearn

MAINTAINER ecoron

RUN pip install SerpScrap --process-dependency-links

ENTRYPOINT python
