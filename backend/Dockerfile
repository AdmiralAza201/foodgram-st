FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=off     PIP_DISABLE_PIP_VERSION_CHECK=on     PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libpq-dev     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

CMD ["/bin/bash","-lc","python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000"]
