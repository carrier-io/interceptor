import json
import os
import time
import re
import shutil
from datetime import datetime
from json import dumps, loads
from subprocess import Popen, PIPE
from time import mktime, sleep
from uuid import uuid4

import docker
from requests import get, put

from interceptor.constants import NAME_CONTAINER_MAPPING, UNZIP_DOCKER_COMPOSE, \
    UNZIP_DOCKERFILE
from interceptor.containers_backend import KubernetesClient
from interceptor.logger import logger as global_logger


class LambdaExecutor:

    def __init__(self, task, event, galloper_url, token, logger=global_logger):
        self.logger = logger
        self.task = task
        self.event = event
        self.galloper_url = galloper_url
        self.token = token
        self.start_time = time.time()

        self.env_vars = loads(self.task.get("env_vars", "{}"))
        if self.task['task_name'] == "control_tower" and "cc_env_vars" in self.event[0]:
            self.env_vars.update(self.event[0]["cc_env_vars"])

        self.artifact_url = f'{self.galloper_url}/api/v1/artifacts/artifact/' \
                            f'{self.task["project_id"]}/{self.task["zippath"]}'
        self.command = [f"{self.task['task_handler']}", dumps(self.event)]

    def execute_lambda(self):
        self.logger.info(f'task {self.task}')
        self.logger.info(f'event {self.event}')
        container_name = NAME_CONTAINER_MAPPING.get(self.task['runtime'])
        if not container_name:
            self.logger.error(f"Container {self.task['runtime']} is not found")
            raise Exception(f"Container {self.task['runtime']} is not found")
        try:
            cloud_settings = self.event["integration"]["clouds"]["kubernetes"]
        except (TypeError, KeyError):
            log, stats = self.execute_in_docker(container_name)
        else:
            log, stats = self.execute_in_kubernetes(container_name, cloud_settings)

        if container_name == "lambda:python3.7":
            results = re.findall(r'({.+?})', log)[-1]
        else:
            # TODO: magic of 2 enters is very flaky, Need to think on how to workaround, probably with specific logging
            results = log.split("\n\n")[1]
        task_result_id = self.task["task_result_id"]
        data = {
            "ts": int(mktime(datetime.utcnow().timetuple())),
            'results': results,
            'log': log,
            'task_duration': time.time() - self.start_time,
            'task_status': "Done" if 200 <= int(json.loads(results).get('statusCode')) <= 299 else "Failed",
            'task_stats': stats
        }
        self.logger.info(f'Task body {data}')
        headers = {
            "Content-Type": "application/json",
            'Authorization': f'bearer {self.token}'}
        res = put(f'{self.galloper_url}/api/v1/tasks/results/{self.task["project_id"]}?task_result_id={task_result_id}',
                  headers=headers, data=dumps(data))
        self.logger.info(f'Created task_results: {res.status_code, res.text}')

        if self.task.get("callback"):
            for each in self.event:
                each['result'] = results
            endpoint = f"/api/v1/task/{self.task['project_id']}/{self.task['callback']}?exec=True"
            headers = {'Authorization': f'bearer {self.token}',
                       'content-type': 'application/json'}
            self.task = get(f"{self.galloper_url}/{endpoint}", headers=headers).json()
            self.execute_lambda()
        self.logger.info('Done.')

    def execute_in_kubernetes(self, container_name, cloud_settings):
        kubernetes_settings = {
            "host": cloud_settings["hostname"],
            "token": cloud_settings["k8s_token"],
            "namespace": cloud_settings["namespace"],
            "jobs_count": 1,
            "logger": self.logger,
            "secure_connection": cloud_settings["secure_connection"]
        }
        client = KubernetesClient(**kubernetes_settings)
        job = client.run_lambda(container_name, self.token, self.env_vars, self.artifact_url,
                                self.command)

        while not job.is_finished():
            sleep(5)
        logs = []
        job.log_status(logs)
        # TODO: grab stats from kubernetes
        return "".join(logs), {}

    def execute_in_docker(self, container_name):
        lambda_id = str(uuid4())
        client = docker.from_env()

        self.download_artifact(lambda_id)
        self.create_volume(client, lambda_id)
        mount = docker.types.Mount(type="volume", source=lambda_id, target="/var/task")
        response = client.containers.run(f"getcarrier/{container_name}",
                                         command=self.command,
                                         mounts=[mount], stderr=True, remove=True,
                                         environment=self.env_vars, detach=True)

        logs = []
        try:
            volume = client.volumes.get(lambda_id)
            volume.remove(force=True)
        except:
            self.logger.info("Failed to remove docker volume")
        shutil.rmtree(f'/tmp/{lambda_id}', ignore_errors=True)
        try:
            self.logger.info(f'container obj {response}')
            log = response.logs(stream=True, follow=True)
            stats = response.stats(decode=None, stream=False)
        except:
            return "\n\n{logs are not available}"
        try:
            while True:
                line = next(log).decode("utf-8", errors='ignore')
                self.logger.info(f'{container_name} - {line}')
                logs.append(line)
        except StopIteration:
            self.logger.info(f'log stream ended for {container_name}')
            logs = ''.join(logs)
            match = re.search(r'memory used: (\d+ \w+).*?', logs, re.I)
            memory = match.group(1) if match else None
            stats["memory_usage"] = memory
            return logs, stats

    def download_artifact(self, lambda_id):
        os.mkdir(f'/tmp/{lambda_id}')
        headers = {'Authorization': f'bearer {self.token}'}
        r = get(self.artifact_url, allow_redirects=True, headers=headers)
        with open(f'/tmp/{lambda_id}/{lambda_id}', 'wb') as file_data:
            file_data.write(r.content)

    def create_volume(self, client, lambda_id):
        client.volumes.create(lambda_id)
        with open(f"/tmp/{lambda_id}/Dockerfile", 'w') as f:
            f.write(
                UNZIP_DOCKERFILE.format(localfile=lambda_id, docker_path=f'{lambda_id}.zip'))
        with open(f"/tmp/{lambda_id}/docker-compose.yaml", 'w') as f:
            f.write(UNZIP_DOCKER_COMPOSE.format(path=f"/tmp/{lambda_id}",
                                                volume=lambda_id, task_id=lambda_id))
        cmd = ['docker-compose', 'up']
        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True,
                      cwd=f"/tmp/{lambda_id}")
        popen.communicate()
        cmd = ['docker-compose', 'down', '--rmi', 'all']
        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True,
                      cwd=f"/tmp/{lambda_id}")
        return popen.communicate()
