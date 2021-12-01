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
    def dast(client, container, execution_params, job_name, *args, **kwargs):
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
            tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
            user="0:0"
        )

    @staticmethod
    def sast(client, container, execution_params, job_name, *args, **kwargs):
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
            tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
            user="0:0"
        )

    @staticmethod
    def perfui(client, container, execution_params, job_name, *args, **kwargs):
        return JobsWrapper.free_style(client, container, execution_params, job_name)

    @staticmethod
    def perfmeter(client, container, execution_params, job_name, *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['loki_host', 'loki_port', 'galloper_url', 'bucket', 'artifact', 'results_bucket', 'additional_files',
                  'JVM_ARGS', 'save_reports', 'project_id', 'token', "report_id"]
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
                                     tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
                                     user='0:0')

    @staticmethod
    def free_style(client, container, execution_params, job_name):
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
                                     tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
                                     user='0:0')

    @staticmethod
    def perfgun(client, container, execution_params, job_name, *args, **kwargs):
        env_vars = {"DISTRIBUTED_MODE_PREFIX": execution_params['DISTRIBUTED_MODE_PREFIX'],
                    "GATLING_TEST_PARAMS": execution_params['GATLING_TEST_PARAMS'],
                    "build_id": execution_params['build_id'],
                    "config_yaml": execution_params['config_yaml']}
        params = ['influxdb_host', 'influxdb_port', 'influxdb_user', 'influxdb_password', 'influxdb_database',
                  'influxdb_comparison', "influxdb_telegraf", 'test_type', 'env', 'loki_host', 'loki_port',
                  'galloper_url', 'bucket', 'test', 'results_bucket', 'artifact', 'additional_files', 'save_reports',
                  'project_id', 'token', 'compile_and_run', 'JVM_ARGS', "report_id"]
        for key in params:
            if key in execution_params.keys():
                env_vars[key] = execution_params[key]

        return client.containers.run(container, name=f'{job_name}_{uuid4()}'[:36],
                                     nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
                                     user='0:0')

    @staticmethod
    def observer(client, container, execution_params, job_name, *args, **kwargs):
        observer_container_name = f'{job_name}_{str(uuid4())[:8]}'
        env_vars = {}
        exclude_vars = ["cmd"]

        for k, v in execution_params.items():
            if k not in exclude_vars:
                env_vars[k] = v

        jira_params = execution_params.get("JIRA")

        if jira_params:
            jira_params = json.loads(jira_params)
            env_vars['JIRA_URL'] = jira_params["jira_url"]
            env_vars['JIRA_USER'] = jira_params["jira_login"]
            env_vars['JIRA_PASSWORD'] = jira_params["jira_password"]
            env_vars['JIRA_PROJECT'] = jira_params["jira_project"]

        ado_params = execution_params.get("ADO")
        if ado_params:
            ado_params = json.loads(ado_params)
            env_vars['ADO_ORGANIZATION'] = ado_params["ado_organization"]
            env_vars['ADO_PROJECT'] = ado_params["ado_project"]
            env_vars['ADO_TOKEN'] = ado_params["ado_token"]
            env_vars['ADO_TEAM'] = ado_params["ado_team"]

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
                                     remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
                                     user='0:0')

    @staticmethod
    def browsertime(client, container, env_vars, cmd, *args, **kwargs):

        return client.containers.run(container, name=f'browsertime_{uuid4()}'[:36],
                                     nano_cpus=c.BROWSERTIME_CPU_QUOTA, mem_limit=c.BROWSERTIME_MEMORY_QUOTA,
                                     command=cmd,
                                     environment=env_vars,
                                     tty=True, detach=True, remove=c.REMOVE_CONTAINERS, auto_remove=c.REMOVE_CONTAINERS,
                                     user='0:0')
