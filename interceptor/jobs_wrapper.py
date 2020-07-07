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
import json


class JobsWrapper(object):
    @staticmethod
    def dast(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
        #
        docker_container = container
        docker_name = f"dast_{uuid4()}"[:36]
        docker_command = execution_params["cmd"]
        docker_environment = {
            "project_id": execution_params["GALLOPER_PROJECT_ID"],
            "galloper_url": execution_params["GALLOPER_URL"],
            "token": execution_params["GALLOPER_AUTH_TOKEN"],
        }
        docker_mounts = list()
        #
        return client.containers.run(
            docker_container, name=docker_name,
            nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
            command=docker_command, environment=docker_environment, mounts=docker_mounts,
            tty=True, detach=True, remove=True, auto_remove=True,
            user="0:0"
        )

    @staticmethod
    def sast(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
        #
        docker_container = container
        docker_name = f"sast_{uuid4()}"[:36]
        docker_command = execution_params["cmd"]
        docker_environment = {
            "project_id": execution_params["GALLOPER_PROJECT_ID"],
            "galloper_url": execution_params["GALLOPER_URL"],
            "token": execution_params["GALLOPER_AUTH_TOKEN"],
        }
        docker_mounts = list()
        #
        return client.containers.run(
            docker_container, name=docker_name,
            nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
            command=docker_command, environment=docker_environment, mounts=docker_mounts,
            tty=True, detach=True, remove=True, auto_remove=True,
            user="0:0"
        )

    @staticmethod
    def perfui(client, container, execution_params, job_name, redis_connection, *args, **kwargs):
        return JobsWrapper.free_style(client, container, execution_params, job_name, redis_connection)

    @staticmethod
    def perfmeter(client, container, execution_params, job_name, redis_connection='', *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['loki_host', 'loki_port', 'galloper_url', 'bucket', 'artifact', 'results_bucket', 'additional_files',
                  'JVM_ARGS', 'save_reports', 'project_id', 'token']
        for key in params:
            if key in execution_params.keys():
                env_vars[key] = execution_params[key]
        if 'mounts' in execution_params.keys():
            mounts = json.loads(execution_params['mounts'])
            docker_mounts = []
            for key, value in mounts.items():
                docker_mounts.append(docker.types.Mount(target=value, source=key, type='bind'))
        else:
            docker_mounts = []
        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=f"{execution_params['cmd']}",
                                     mounts=docker_mounts,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')

    @staticmethod
    def free_style(client, container, execution_params, job_name, redis_connection=''):
        if 'mounts' in execution_params.keys():
            mounts = json.loads(execution_params['mounts'])
            docker_mounts = []
            for key, value in mounts.items():
                docker_mounts.append(docker.types.Mount(target=value, source=key, type='bind'))
        else:
            docker_mounts = []
        command = execution_params.pop("cmd", "")
        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=command,
                                     mounts=docker_mounts,
                                     environment=execution_params,
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')

    @staticmethod
    def perfgun(client, container, execution_params, job_name, redis_connection='', *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "GATLING_TEST_PARAMS": execution_params['GATLING_TEST_PARAMS'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['influxdb_host', 'influxdb_port', 'influxdb_user', 'influxdb_password', 'influxdb_database',
                  'influxdb_comparison', 'test_type', 'env', 'loki_host', 'loki_port', 'galloper_url', 'bucket',
                  'test', 'results_bucket', 'artifact', 'additional_files', 'save_reports', 'project_id', 'token']
        for key in params:
            if key in execution_params.keys():
                env_vars[key] = execution_params[key]

        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=True, auto_remove=True, user='0:0')

    @staticmethod
    def observer(client, container, execution_params, job_name, redis_connection='', *args, **kwargs):
        observer_container_name = f'{job_name}_{str(uuid4())[:8]}'

        env_vars = {
            "REMOTE_URL": execution_params['REMOTE_URL'],
            "LISTENER_URL": execution_params['LISTENER_URL'],
            "GALLOPER_URL": execution_params["GALLOPER_URL"],
            "GALLOPER_PROJECT_ID": execution_params["GALLOPER_PROJECT_ID"],
            "RESULTS_BUCKET": execution_params["RESULTS_BUCKET"],
            "RESULTS_REPORT_NAME": execution_params["RESULTS_REPORT_NAME"]
        }

        variables = ['token', "REPORTS_BUCKET", "TESTS_BUCKET", "ENV", "EXPORTERS_PATH"]

        for var_name in variables:
            if var_name in execution_params.keys():
                env_vars[var_name] = execution_params[var_name]

        jira_params = execution_params.get("JIRA")

        if jira_params:
            jira_params = json.loads(jira_params)
            env_vars['JIRA_URL'] = jira_params["jira_url"]
            env_vars['JIRA_USER'] = jira_params["jira_login"]
            env_vars['JIRA_PASSWORD'] = jira_params["jira_password"]
            env_vars['JIRA_PROJECT'] = jira_params["jira_project"]

        docker_mounts = []

        if 'mounts' in execution_params.keys():
            for mount in execution_params['mounts']:
                for key, value in mount.items():
                    docker_mounts.append(docker.types.Mount(target=value, source=key, type='bind'))

        observer_command = execution_params['cmd']

        return client.containers.run(container, name=observer_container_name, nano_cpus=c.CONTAINER_CPU_QUOTA,
                                     mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     command=observer_command,
                                     environment=env_vars,
                                     mounts=docker_mounts,
                                     tty=True, detach=True,
                                     remove=True, auto_remove=True,
                                     user='0:0')
