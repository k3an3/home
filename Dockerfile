FROM python:3.6

ADD requirements.txt /tmp
RUN useradd user
RUN pip3 install -r /tmp/requirements.txt
ADD . /app

USER user
CMD ["/app/scripts/run.sh"]
