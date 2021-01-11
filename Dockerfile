FROM ubuntu:latest

RUN apt-get update -y
RUN apt-get install -y python3-pip python3

RUN pip3 install flask flask-sqlalchemy flask-login psycopg2-binary

WORKDIR /app
