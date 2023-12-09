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


interceptor_conf = """[supervisord]
nodaemon=true

[program:worker]
command=run
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true
"""


def main():
    import os
    supervisor_conf_path = os.environ.get("SUPERVISOR_CONF_PATH", "/etc/interceptor.conf")
    with open(supervisor_conf_path, 'w') as f:
        f.write(interceptor_conf)
