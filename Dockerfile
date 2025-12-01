FROM python:3.11-alpine

RUN apk update && apk add --no-cache supervisor docker docker-compose git bash gcc g++ linux-headers

WORKDIR /tmp

# Copy requirements and source code
COPY requirements.txt .
COPY setup.py .
COPY interceptor ./interceptor
COPY start.sh .

RUN chmod +x start.sh

# Install everything in one step
RUN pip install --upgrade pip setuptools \
    && pip install . \
    && rm -rf interceptor requirements.txt setup.py

RUN pip install git+https://github.com/carrier-io/arbiter.git
RUN pip install git+https://github.com/carrier-io/loki_logger.git

SHELL ["/bin/bash", "-c"]

ENTRYPOINT ["/tmp/start.sh"]

