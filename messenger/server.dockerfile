FROM python:3.8-slim

WORKDIR /02-practice-grpc/messenger/
COPY server/requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir messenger
COPY __init__.py messenger/__init__.py
COPY server/ messenger/server-py/
COPY proto messenger/proto/

ENTRYPOINT ["python", "-m", "messenger.server-py.server"]
