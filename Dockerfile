FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
RUN mkdir -p /app/uploads

EXPOSE 10000
ENV PORT=10000

CMD ["sh", "-c", "gunicorn --workers ${WEB_CONCURRENCY:-1} --worker-class gevent --worker-connections 100 --timeout 300 --graceful-timeout 30 -b 0.0.0.0:${PORT:-10000} app:app"]
