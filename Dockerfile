FROM python:3.8.14-alpine3.16

WORKDIR /app
COPY requirements.txt requirements.txt
RUN apk add --no-cache zip && pip3 install -r requirements.txt
COPY . /app/
EXPOSE 80