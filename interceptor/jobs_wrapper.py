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

import docker

from uuid import uuid4
from interceptor import constants as c


class JobsWrapper(object):
    @staticmethod
    def dast(container, execution_params, job_name, redis_connection, *args, **kwargs):
        client = docker.from_env()
        required_keys = ['host', 'port', 'protocol', 'test_type']
        if not all(k in execution_params for k in required_keys):
            return False, "Missing required params (%s)" % ",".join(required_keys)
        if not [container] in [k.tags for k in client.images.list()]:
            return False, "Please specify proper tag of security container e.g. getcarrier/dast:latest"
        host = execution_params.get('host')
        port = execution_params.get('port')
        protocol = execution_params.get('protocol')
        project = execution_params.get('project', job_name)
        environment = execution_params.get('environment', "default")
        # redis_connection = ''
        client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                              nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                              command=f"-s {execution_params['test_type']}",
                              environment={"host": host, "port": port,
                                           "protocol": protocol, "project_name": project,
                                           "environment": environment,
                                           "redis_connection": redis_connection},
                              remove=True)
        return True, "Done"

    @staticmethod
    def sast(container, execution_params, job_name, redis_connection, *args, **kwargs):
        pass

    @staticmethod
    def perfui(container, execution_params, job_name, redis_connection, *args, **kwargs):
        return JobsWrapper.free_style(container, execution_params, job_name, redis_connection)

    @staticmethod
    def perfmeter(container, execution_params, job_name, redis_connection='',  *args, **kwargs):
        return JobsWrapper.free_style(container, execution_params, job_name, redis_connection)

    @staticmethod
    def free_style(container, execution_params, job_name, redis_connection=''):
        client = docker.from_env()
        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=f"{execution_params['cmd']}",
                                     environment={"redis_connection": redis_connection},
                                     tty=True, detach=True)

    @staticmethod
    def perfgun(container, execution_params, job_name, redis_connection='', *args, **kwargs):
        return JobsWrapper.free_style(container, execution_params, job_name, redis_connection)
