import json
from typing import Optional

import requests

from interceptor.constants import POSTPROCESSOR_CONTAINER
from interceptor.containers_backend import DockerClient, KubernetesClient
from interceptor.logger import logger as global_logger
from interceptor.utils import build_api_url


class PostProcessor:

    def __init__(
            self, galloper_url: str, project_id: int, galloper_web_hook: str,
            report_id, build_id: str, bucket: str, prefix: str,
            logger=global_logger, token: Optional[str] = None,
            integrations: dict | str | None = None,
            exec_params: Optional[dict] = None,
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
        if not integrations:
            self.integrations = dict()
        elif isinstance(integrations, str):
            self.integrations = json.loads(integrations)
        else:
            self.integrations = integrations
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

    @property
    def env_vars(self) -> dict:
        return {
            "base_url": self.galloper_url,
            "token": self.token,
            "project_id": self.project_id,
            "bucket": self.bucket,
            "build_id": self.build_id,
            "report_id": self.report_id,
            "integrations": self.integrations,
            "exec_params": self.exec_params
        }

    @property
    def kubernetes_settings(self) -> Optional[dict]:
        return self.integrations.get('clouds', {}).get('kubernetes')

    def results_post_processing(self):
        if self.kubernetes_settings:
            client = KubernetesClient(**{
                "host": self.kubernetes_settings["hostname"],
                "token": self.kubernetes_settings["k8s_token"],
                "namespace": self.kubernetes_settings["namespace"],
                "jobs_count": 1,
                "logger": self.logger,
                "secure_connection": self.kubernetes_settings["secure_connection"],
                "mode": self.mode
            })
            job = client.run(
                POSTPROCESSOR_CONTAINER,
                name="post-processing",
                environment=self.env_vars,
                command="",
                nano_cpus=self.kubernetes_settings["post_processor_cpu_cores_limit"] * 1000000000,
                mem_limit=f"{self.kubernetes_settings['post_processor_memory_limit']}G",
            )
        else:
            client = DockerClient(self.logger)

            job = client.run(POSTPROCESSOR_CONTAINER,
                             stderr=True, remove=True, detach=True,
                             environment=self.env_vars)

        return job
