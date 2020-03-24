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

from uuid import uuid4
from interceptor import constants as c
import docker


class JobsWrapper(object):
    @staticmethod
    def dast(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
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
    def sast(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
        pass

    @staticmethod
    def perfui(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
        return JobsWrapper.free_style(client, container, execution_params, job_name, redis_connection)

    @staticmethod
    def perfmeter(client, container, execution_params, job_name, redis_connection='',  *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['loki_host', 'loki_port', 'galloper_url', 'bucket', 'artifact', 'results_bucket', 'additional_files',
                  'JVM_ARGS', 'save_reports', 'project_id']
        for key in params:
            if key in execution_params.keys():
                env_vars[key] = execution_params[key]
        if 'mount_target' in execution_params.keys() and 'mount_source' in execution_params.keys():
            mounts = [docker.types.Mount(target=execution_params['mount_target'],
                                         source=execution_params['mount_source'], type='bind')]
        else:
            mounts = []
        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=f"{execution_params['cmd']}",
                                     mounts=mounts,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')

    @staticmethod
    def free_style(client, container, execution_params, job_name, redis_connection=''):
        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=f"{execution_params['cmd']}",
                                     environment={"redis_connection": redis_connection},
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')

    @staticmethod
    def perfgun(client, container, execution_params, job_name, redis_connection='', *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "GATLING_TEST_PARAMS": execution_params['GATLING_TEST_PARAMS'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['influxdb_host', 'influxdb_port', 'influxdb_user', 'influxdb_password', 'influxdb_database',
                  'influxdb_comparison', 'test_type', 'env', 'loki_host', 'loki_port', 'galloper_url', 'bucket',
                  'test', 'results_bucket', 'artifact', 'additional_files', 'save_reports', 'project_id']
        for key in params:
            if key in execution_params.keys():
                env_vars[key] = execution_params[key]

        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')
