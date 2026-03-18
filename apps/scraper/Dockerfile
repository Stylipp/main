FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx beautifulsoup4 aiosqlite pyyaml

COPY apps/scraper/ .

VOLUME /app/data

ENTRYPOINT ["python", "run.py"]
