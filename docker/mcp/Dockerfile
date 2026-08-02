FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.lock pyproject.toml README.rst LICENSE MANIFEST.in ./
COPY serpscrap ./serpscrap
COPY scrapcore ./scrapcore

RUN pip install --no-cache-dir -r requirements.lock && \
    pip install --no-cache-dir --no-deps .

EXPOSE 8001
ENTRYPOINT ["python", "-m", "serpscrap.mcp_server"]
