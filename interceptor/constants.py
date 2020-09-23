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
CONTAINER_CPU_QUOTA = int(environ.get('CPU_QUOTA', 1)) * CPU_MULTIPLIER  # nano fraction of single core
CONTAINER_MEMORY_QUOTA = environ.get('RAM_QUOTA', '1g')
LOKI_HOST = environ.get('LOKI_HOST', "")
LOKI_PORT = int(environ.get('LOKI_PORT', 3100))
LOG_LEVEL = environ.get('LOG_LEVEL', 'info')
REMOVE_CONTAINERS = True if environ.get("REMOVE_CONTAINERS", "True") == "True" else False
