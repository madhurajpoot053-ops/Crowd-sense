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

EXPOSE 5000
ENV PORT=5000

CMD ["sh", "-c", "gunicorn -w 2 --threads 2 -k gthread --timeout 120 --graceful-timeout 120 -b 0.0.0.0:${PORT:-5000} app:app"]
