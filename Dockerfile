FROM ecoron/python36-sklearn

MAINTAINER ecoron

RUN pip uninstall SerpScrap -y
RUN pip install SerpScrap

ENTRYPOINT python
