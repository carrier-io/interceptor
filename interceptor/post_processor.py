import json
from typing import Optional

import requests

from interceptor.constants import POSTPROCESSOR_CONTAINER
from interceptor.containers_backend import DockerClient, KubernetesClient
from interceptor.logger import logger as global_logger
from interceptor.utils import build_api_url
from interceptor import constants as c


class PostProcessor:

    @staticmethod
    def handle_json_dict(json_dict: dict | str | None = None) -> dict:
        if not json_dict:
            return dict()
        elif isinstance(json_dict, str):
            return json.loads(json_dict)
        else:
            return json_dict

    def __init__(
            self, galloper_url: str, project_id: int,
            report_id, build_id: str, bucket: str,
            logger=global_logger, token: Optional[str] = None,
            integrations: dict | str | None = None,
            exec_params: dict | str | None = None,
            mode: str = 'default', **kwargs
    ):
        self.logger = logger
        self.galloper_url = galloper_url
        self.project_id = project_id
        self.build_id = build_id
        self.bucket = bucket
        self.config_file = '{}'
        self.token = token
        self.integrations = self.handle_json_dict(integrations)
        self.exec_params = self.handle_json_dict(exec_params)
        self.report_id = report_id
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
            "integrations": json.dumps(self.integrations),
            "exec_params": json.dumps(self.exec_params)
        }

    @property
    def kubernetes_settings(self) -> Optional[dict]:
        return self.integrations.get('clouds', {}).get('kubernetes')

    def results_post_processing(self):
        if self.kubernetes_settings:
            client = KubernetesClient(**{
                "host": kubernetes_settings["hostname"],
                "token": kubernetes_settings["k8s_token"],
                "namespace": kubernetes_settings["namespace"],
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
                nano_cpus=self.kubernetes_settings["post_processor_cpu_cores_limit"] * c.CPU_MULTIPLIER,
                mem_limit=f"{self.kubernetes_settings['post_processor_memory_limit']}G",
            )
        else:
            # exec_params = json.loads(self.exec_params)
            # nano_cpus = int(float(exec_params["cpu_quota"]) * c.CPU_MULTIPLIER) if exec_params.get(
            #     "cpu_quota") else c.CONTAINER_CPU_QUOTA
            # mem_limit = f'{exec_params["memory_quota"]}g' if exec_params.get(
            #     "memory_quota") else c.CONTAINER_MEMORY_QUOTA
            client = DockerClient(self.logger)

            job = client.run(
                POSTPROCESSOR_CONTAINER,
                stderr=True, remove=True, detach=True,
                environment=self.env_vars,
                nano_cpus=nano_cpus, mem_limit=mem_limit
            )

        return job
