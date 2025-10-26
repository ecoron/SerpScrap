------
Docker
------

You can run SerpScrap easily with Docker. The provided Dockerfile uses a modern, minimal Python 3.10 base image and installs all required dependencies, including Google Chrome and chromedriver.

Build the Docker image:

.. code-block:: bash

   docker build -t serpscrap .

Run SerpScrap using the CLI inside the container:

.. code-block:: bash

   docker run --rm -it serpscrap python -m serpscrap.cli --keywords "example keyword"

To mount your own configuration or keyword files, use a volume:

.. code-block:: bash

   docker run --rm -v /path/to/your/config:/serpscrap/config serpscrap python -m serpscrap.cli --config /serpscrap/config/your_config.json

The image is based on python:3.10-slim and is suitable for both development and production use.

Docker Hub: https://hub.docker.com/r/ecoron/serpscrap/
