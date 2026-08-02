FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY ui /ui

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/index.html')"
ENTRYPOINT ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/ui"]
