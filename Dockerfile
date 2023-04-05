FROM python:3.11-alpine

#ENV GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
#ENV GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1

RUN apk update && apk add --no-cache supervisor docker docker-compose git bash g++
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

ADD setup.py /tmp/setup.py
ADD requirements.txt /tmp/requirements.txt
COPY interceptor /tmp/interceptor

RUN pip install requests
RUN pip install grpcio  # to fail fast
RUN cd /tmp && python setup.py install && rm -rf /tmp/interceptor /tmp/requirements.txt /tmp/setup.py
ADD start.sh /tmp/start.sh
RUN chmod +x /tmp/start.sh
RUN pip install git+https://github.com/carrier-io/arbiter.git
RUN pip install git+https://github.com/carrier-io/loki_logger.git

SHELL ["/bin/bash", "-c"]

ENTRYPOINT ["/tmp/start.sh"]
