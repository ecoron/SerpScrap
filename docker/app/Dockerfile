FROM python:3.12-slim

ARG CHROME_FOR_TESTING_VERSION=151.0.7922.71

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERPSCRAP_CHROME_BINARY=/opt/chrome/chrome \
    SERPSCRAP_CHROMEDRIVER=/usr/local/bin/chromedriver \
    SERPSCRAP_CHROME_NO_SANDBOX=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl unzip \
      fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
      libcups2 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 libgtk-3-0 \
      libnspr4 libnss3 libu2f-udev libvulkan1 libx11-6 libxcb1 \
      libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 \
      libxrandr2 xdg-utils && \
    curl --fail --location --silent --show-error \
      "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_FOR_TESTING_VERSION}/linux64/chrome-linux64.zip" \
      --output /tmp/chrome.zip && \
    curl --fail --location --silent --show-error \
      "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_FOR_TESTING_VERSION}/linux64/chromedriver-linux64.zip" \
      --output /tmp/chromedriver.zip && \
    unzip -q /tmp/chrome.zip -d /opt && \
    unzip -q /tmp/chromedriver.zip -d /opt && \
    mv /opt/chrome-linux64 /opt/chrome && \
    mv /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod 0755 /opt/chrome/chrome /usr/local/bin/chromedriver && \
    rm -rf /var/lib/apt/lists/* /tmp/chrome.zip /tmp/chromedriver.zip \
      /opt/chromedriver-linux64

WORKDIR /app
COPY requirements.lock pyproject.toml README.rst LICENSE MANIFEST.in ./
COPY serpscrap ./serpscrap
COPY scrapcore ./scrapcore

RUN pip install --no-cache-dir -r requirements.lock && \
    pip install --no-cache-dir --no-deps .

HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=2 \
  CMD python -c "from scrapcore.scraper.browser import ChromeDriverFactory; from serpscrap.config import Config; d=ChromeDriverFactory.from_config(Config().get()).create(); d.quit()"

ENTRYPOINT ["serpscrap"]
CMD ["--help"]
