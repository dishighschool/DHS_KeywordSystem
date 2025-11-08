FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=development \
    FLASK_APP=app:create_app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
    && pip install .

EXPOSE 5000

ENTRYPOINT ["gunicorn","-b","0.0.0.0:5000", "wsgi:app"]