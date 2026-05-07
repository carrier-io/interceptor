FROM python:3.11-alpine

# Install system dependencies (excluding old docker-compose)
RUN apk update && apk add --no-cache supervisor docker git bash gcc g++ linux-headers wget

# Install Docker Compose V2 plugin
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    wget -O /usr/local/lib/docker/cli-plugins/docker-compose \
      https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose && \
    ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    wget -O /usr/local/lib/docker/cli-plugins/docker-buildx \
      https://github.com/docker/buildx/releases/download/v0.33.0/buildx-v0.33.0.linux-amd64 && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools

ADD setup.py /tmp/setup.py
ADD requirements.txt /tmp/requirements.txt
COPY interceptor /tmp/interceptor
ADD start.sh /tmp/start.sh
RUN chmod +x /tmp/start.sh

WORKDIR /tmp
RUN pip install requests
RUN python setup.py install
RUN rm -rf interceptor requirements.txt setup.py
RUN pip install git+https://github.com/carrier-io/arbiter.git
RUN pip install git+https://github.com/carrier-io/loki_logger.git
RUN pip install \
    urllib3==1.26.15 \
    requests==2.31.0 \
    docker==7.1.0 \
    PyYAML==6.0.1 \
    redis==4.6.0 \
    python-logging-loki==0.3.1 \
    boto3==1.27.0 \
    requests-mock==1.10.0 \
    mock==5.0.1 \
    kubernetes==26.1.0 \
    google-cloud-compute==1.11.0 \
    google-auth==2.21.0 \
    grpcio-status==1.49.1 \
    protobuf==4.21.12

SHELL ["/bin/bash", "-c"]

ENTRYPOINT ["/tmp/start.sh"]
