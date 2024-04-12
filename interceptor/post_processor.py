import json
from os import path, environ
from typing import Optional

import docker
import requests

from interceptor.containers_backend import DockerClient, KubernetesClient
from interceptor.lambda_executor import LambdaExecutor
from interceptor.logger import logger as global_logger
from interceptor.utils import build_api_url


class PostProcessor:

    def __init__(
            self, galloper_url: str, project_id: int, galloper_web_hook: str,
            report_id, build_id: str, bucket: str, prefix: str,
            logger=global_logger, token: Optional[str] = None,
            integration: Optional[list] = None, exec_params: Optional[dict] = None,
            mode: str = 'default', **kwargs
    ):
        self.logger = logger
        self.galloper_url = galloper_url
        self.project_id = project_id
        self.galloper_web_hook = galloper_web_hook
        self.build_id = build_id
        self.bucket = bucket
        self.prefix = prefix
        self.config_file = '{}'
        self.token = token
        self.integration = integration if integration else []
        self.report_id = report_id
        self.exec_params = exec_params if exec_params else {}
        self.mode = mode
        self.api_version = kwargs.get('api_version', 1)
        self.api_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'{kwargs.get("token_type", "bearer")} {self.token}'
        }

    def update_test_status(self, status, percentage, description):
        data = {"test_status": {"status": status, "percentage": percentage,
                                "description": description}}
        status_url = build_api_url('backend_performance', 'report_status', mode=self.mode,
                                   api_version=self.api_version)
        url = f'{self.galloper_url}{status_url}/' \
              f'{self.project_id}/{self.report_id}'
        response = requests.put(url, json=data, headers=self.api_headers)
        try:
            self.logger.info(response.json()["message"])
        except:
            self.logger.info(response.text)

    def results_post_processing_old(self):
        if self.galloper_web_hook:
            if path.exists('/tmp/config.yaml'):
                with open("/tmp/config.yaml", "r") as f:
                    self.config_file = f.read()
            else:
                self.config_file = environ.get('CONFIG_FILE', '{}')

            event = {'galloper_url': self.galloper_url, 'project_id': self.project_id,
                     'config_file': json.dumps(self.config_file),
                     'bucket': self.bucket, 'prefix': self.prefix, 'token': self.token,
                     'integration': self.integration, "report_id": self.report_id}
            task_url = build_api_url('tasks', 'task', mode=self.mode,
                                     api_version=self.api_version)
            endpoint = f"{task_url}/{self.project_id}/" \
                       f"{self.galloper_web_hook.replace(self.galloper_url + '/task/', '')}?exec=True"
            task = requests.get(f"{self.galloper_url}{endpoint}",
                                headers=self.api_headers).json()
            try:
                LambdaExecutor(task, event, self.galloper_url, self.token,
                               self.logger).execute_lambda()
            except Exception as exc:
                self.update_test_status("Error", 100, f"Failed to start postprocessing")
                raise exc

    def results_post_processing(self):

        env_vars = {"base_url": self.galloper_url, "token": self.token,
                    'galloper_url': self.galloper_url,
                    "project_id": self.project_id,
                    "bucket": self.bucket, "build_id": self.build_id,
                    "report_id": self.report_id,
                    "integrations": self.integration, "exec_params": self.exec_params}


        post_processor_container = environ.get("post_processor_container", "getcarrier/performance_results_processing:beta-1.0")
        if kubernetes_settings := json.loads(
                self.integration).get("clouds", {}).get("kubernetes", {}):

            client = KubernetesClient(**{
                "host": kubernetes_settings["hostname"],
                "token": kubernetes_settings["k8s_token"],
                "namespace": kubernetes_settings["namespace"],
                "jobs_count": 1,
                "logger": self.logger,
                "secure_connection": kubernetes_settings["secure_connection"],
                "mode": self.mode
            })
            job = client.run(
                post_processor_container,
                name="post-processing",
                environment=env_vars,
                command="",
                nano_cpus=kubernetes_settings["post_processor_cpu_cores_limit"] * 1000000000,
                mem_limit=f"{kubernetes_settings['post_processor_memory_limit']}G",
            )
        else:
            client = DockerClient(self.logger)

            job = client.run(post_processor_container,
                             stderr=True, remove=True, detach=True,
                             environment=env_vars)

        return job
