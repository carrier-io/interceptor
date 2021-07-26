import os
from uuid import uuid4
import shutil
from json import dumps, loads
from requests import post, get
from datetime import datetime
from time import mktime
import re
import docker
from traceback import format_exc
from subprocess import Popen, PIPE
import logging
from interceptor.constants import NAME_CONTAINER_MAPPING, UNZIP_DOCKER_COMPOSE, UNZIP_DOCKERFILE


class LambdaExecutor:

    def __init__(self, task, event, galloper_url, token):
        self.task = task
        self.event = event
        self.galloper_url = galloper_url
        self.token = token

    def execute_lambda(self):
        lambda_id = str(uuid4())
        client = docker.from_env()
        container_name = NAME_CONTAINER_MAPPING.get(self.task['runtime'])
        if not container_name:
            return f"Container {self.task['runtime']} is not found"
        self.download_artifact(lambda_id)
        self.create_volume(client, lambda_id)
        mount = docker.types.Mount(type="volume", source=lambda_id, target="/var/task")
        env_vars = loads(self.task.get("env_vars", "{}"))
        if self.task['task_name'] == "control_tower" and "cc_env_vars" in self.event[0]:
            env_vars.update(self.event[0]["cc_env_vars"])
        response = client.containers.run(f"getcarrier/{container_name}",
                                         command=[f"{self.task['task_handler']}", dumps(self.event)],
                                         mounts=[mount], stderr=True, remove=True,
                                         environment=env_vars)
        try:
            volume = client.volumes.get(lambda_id)
            volume.remove(force=True)
        except:
            logging.info("Failed to remove docker volume")
        shutil.rmtree(f'/tmp/{lambda_id}', ignore_errors=True)
        try:
            log = response.decode("utf-8", errors='ignore')
        except:
            log = "\n\n{logs are not available}"
        if container_name == "lambda:python3.7":
            results = re.findall(r'({.+?})', log)[-1]
        else:
            # TODO: magic of 2 enters is very flaky, Need to think on how to workaround, probably with specific logging
            results = log.split("\n\n")[1]

        data = {"ts": int(mktime(datetime.utcnow().timetuple())), 'results': results, 'stderr': log}

        headers = {
            "Content-Type": "application/json",
            'Authorization': f'bearer {self.token}'}
        post(f'{self.galloper_url}/api/v1/task/{self.task["task_id"]}/results', headers=headers, data=dumps(data))
        # if self.task["callback"]:
        #     for each in self.event:
        #         each['result'] = results
        #     endpoint = f"/api/v1/task/{self.task['project_id']}/{self.task['callback']}?exec=True"
        #     headers = {'Authorization': f'bearer {self.token}', 'content-type': 'application/json'}
        #     self.task = get(f"{self.galloper_url}/{endpoint}", headers=headers).json()
        #     self.execute_lambda()

    def download_artifact(self, lambda_id):
        try:
            os.mkdir(f'/tmp/{lambda_id}')
            endpoint = f'/api/v1/artifact/{self.task["project_id"]}/{self.task["zippath"]}'
            headers = {'Authorization': f'bearer {self.token}'}
            r = get(f'{self.galloper_url}/{endpoint}', allow_redirects=True, headers=headers)
            with open(f'/tmp/{lambda_id}/{lambda_id}', 'wb') as file_data:
                file_data.write(r.content)
        except Exception:
            print(format_exc())

    def create_volume(self, client, lambda_id):
        client.volumes.create(lambda_id)
        with open(f"/tmp/{lambda_id}/Dockerfile", 'w') as f:
            f.write(UNZIP_DOCKERFILE.format(localfile=lambda_id, docker_path=f'{lambda_id}.zip'))
        with open(f"/tmp/{lambda_id}/docker-compose.yaml", 'w') as f:
            f.write(UNZIP_DOCKER_COMPOSE.format(path=f"/tmp/{lambda_id}",
                                                volume=lambda_id, task_id=lambda_id))
        cmd = ['docker-compose', 'up']
        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=f"/tmp/{lambda_id}")
        popen.communicate()
        cmd = ['docker-compose', 'down', '--rmi', 'all']
        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True, cwd=f"/tmp/{lambda_id}")
        return popen.communicate()
