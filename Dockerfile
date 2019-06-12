FROM python:3.7-slim-stretch
LABEL maintainer "joshschertz3@gmail.com"

# Create and set password for uwsgi user
#RUN useradd --create-home --shell /bin/bash uwsgi
#RUN echo 'uwsgi:wrong-horse-battery-staple' | chpasswd
#USER uwsgi

WORKDIR /flasker

RUN apt-get update && apt-get install -y build-essential python3-dev
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app
COPY migrations migrations
COPY flasker.py config.py uwsgi.ini wsgi.py ./

ENV FLASK_APP flasker.py

# Upgrade the database and start the Flask app
CMD flask db upgrade && uwsgi --ini uwsgi.ini
