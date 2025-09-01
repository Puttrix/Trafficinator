# Lightweight image with deps baked in
FROM python:3.11-alpine

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY loader.py /app/loader.py

# Copy config files into the container
COPY ../config /config

# A basic healthcheck: process is alive and DNS can resolve the host in MATOMO_URL (optional best-effort)
HEALTHCHECK --interval=1m --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import os,sys,urllib.parse,socket; u=urllib.parse.urlparse(os.getenv('MATOMO_URL','')); \
host=u.hostname or 'localhost'; socket.getaddrinfo(host, None); sys.exit(0)" || exit 1

CMD ["python", "/app/loader.py"]
