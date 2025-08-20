FROM python:3.13-alpine

RUN addgroup -S python && adduser -S python -G python

WORKDIR /home/python

COPY ./requirements.txt /home/python/requirements.txt
RUN pip install --no-cache-dir -r /home/python/requirements.txt

COPY --chown=python:python . /home/python/

USER python:python

EXPOSE 5000

CMD ["python", "/home/python/app.py"]