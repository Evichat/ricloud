FROM python:2.7-slim

LABEL version="1.0" description="Ricloud" maintainer="xyz@poop.ca"

RUN mkdir -p /copypastafolder
COPY . /copypastafolder
WORKDIR /copypastafolder

RUN pip2 install -r requirements.txt
# RUN pip2 install python-mysqldb

CMD python -m ricloud --listen
