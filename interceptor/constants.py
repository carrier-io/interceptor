#   Copyright 2018 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from os import environ


CPU_MULTIPLIER = 1000000000
CONTAINER_CPU_QUOTA = int(float(environ.get('CPU_QUOTA', 1)) * CPU_MULTIPLIER)  # nano fraction of single core
BROWSERTIME_CPU_QUOTA = int(environ.get('BROWSERTIME_CPU_QUOTA', 2)) * CPU_MULTIPLIER  # nano fraction of single core
CONTAINER_MEMORY_QUOTA = environ.get('RAM_QUOTA', '1g')
BROWSERTIME_MEMORY_QUOTA = environ.get('BROWSERTIME_MEMORY_QUOTA', '4g')
LOKI_HOST = environ.get('LOKI_HOST', "")
LOKI_PORT = int(environ.get('LOKI_PORT', 3100))
LOG_LEVEL = environ.get('LOG_LEVEL', 'info')
REMOVE_CONTAINERS = True if environ.get("REMOVE_CONTAINERS", "True") == "True" else False
PYLON_URL = environ.get('PYLON_URL')
LAMBDA_DOCKER_NETWORK = environ.get("LAMBDA_DOCKER_NETWORK", "").strip()
LAMBDA_DOCKER_NETWORK_MODE = environ.get("LAMBDA_DOCKER_NETWORK_MODE", "").strip()


NAME_CONTAINER_MAPPING = {
    "Python 3.8": 'lambda:python3.8',
    "Python 3.7": 'lambda:python3.7',
    "Python 3.6": 'lambda:python3.6',
    "Python 2.7": 'lambda:python2.7',
    ".NET Core 2.0 (C#)": 'lambda:dotnetcore2.0',
    ".NET Core 2.1 (C#/PowerShell)": 'lambda:dotnetcore2.1',
    "Go 1.x": "lambda:go1.x",
    "Java 8": "lambda:java8",
    "Java 11": "lambda:java11",
    "Node.js 6.10": 'lambda:nodejs6.10',
    "Node.js 8.10": 'lambda:nodejs8.10',
    "Node.js 10.x": 'lambda:nodejs10.x',
    "Node.js 12.x": 'lambda:nodejs12.x',
    "Ruby 2.5": 'lambda:ruby2.5'
}

LAMBDA_CONTAINER_REPO = environ.get('LAMBDA_CONTAINER_REPO', 'getcarrier')
BROWSERTIME_CONTAINER = environ.get('BROWSERTIME_CONTAINER', 'getcarrier/browsertime:latest')
POSTPROCESSOR_CONTAINER = environ.get('POSTPROCESSOR_CONTAINER', 'getcarrier/performance_results_processing:latest')
STRIP_HEADERS = ["content-length"]


SSL_CERTS = environ.get('SSL_CERTS', '')
ARBITER_RUNTIME = environ.get('ARBITER_RUNTIME', 'rabbitmq')
EVENT_NODE_WORKERS = int(environ.get('EVENT_NODE_WORKERS', '1'))
TASK_NODE_MP_CONTEXT = environ.get('TASK_NODE_MP_CONTEXT', 'fork')
EXECUTOR_RUNTIME = environ.get('EXECUTOR_RUNTIME', 'default')
K8S_MOUNT_TMP = environ.get("K8S_MOUNT_TMP", "").lower() in ["true", "yes"]
K8S_STOP_JOBS = environ.get("K8S_STOP_JOBS", "").lower() in ["true", "yes"]

RABBIT_USER = environ.get('RABBIT_USER', 'user')
RABBIT_PASSWORD = environ.get('RABBIT_PASSWORD', 'password')
RABBIT_HOST = environ.get('RABBIT_HOST', 'localhost')
RABBIT_PORT = int(environ.get('RABBIT_PORT', '5672'))
RABBIT_USE_SSL = environ.get("RABBIT_USE_SSL", "").lower() in ["true", "yes"]
RABBIT_SSL_VERIFY = environ.get("RABBIT_SSL_VERIFY", "").lower() in ["true", "yes"]

REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(environ.get('REDIS_PORT', '6379'))
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', '')
REDIS_USE_SSL = environ.get("REDIS_USE_SSL", "").lower() in ["true", "yes"]

SIO_URL = environ.get('SIO_URL', '')
SIO_PASSWORD = environ.get('SIO_PASSWORD', '')
SIO_SSL_VERIFY = environ.get("SIO_SSL_VERIFY", "").lower() in ["true", "yes"]

QUEUE_NAME = environ.get('QUEUE_NAME', "default")
CPU_CORES = environ.get('CPU_CORES', 2)
VHOST = environ.get('VHOST', 'carrier')
TOKEN = environ.get('TOKEN', '')
