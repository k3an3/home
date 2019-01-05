FROM python:3.6

ADD requirements.txt /tmp
RUN useradd -u 1002 home
RUN pip3 install -r /tmp/requirements.txt
RUN apt -o Acquire::ForceIPv4=true update && apt install -o Acquire::ForceIPv4=true -y redis-server
RUN pip3 install -U redis==2.10.6

USER home
CMD ["/app/scripts/run.sh"]
