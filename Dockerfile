FROM python:3.8-alpine

RUN apk add --no-cache --virtual .build-deps gcc postgresql-dev musl-dev python3-dev
RUN apk add libpq

RUN mkdir -p /app/src
COPY src/ /app/src/

RUN mkdir -p /app/tests
COPY tests/ /app/tests/

COPY Pipfile /app/
COPY Pipfile.lock /app/

RUN pip install pipenv
RUN cd /app && pipenv install --system --deploy --ignore-pipfile

WORKDIR /app/src
ENV FLASK_APP=allocation/entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1
CMD flask run --host=0