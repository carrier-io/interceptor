import json
from typing import Optional, Iterable

from interceptor.constants import POSTPROCESSOR_CONTAINER
from interceptor.containers_backend import DockerClient, KubernetesClient
from interceptor.logger import logger as global_logger


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
            mode: str = 'default', manual_run: bool = False,
            logger_stop_words: Iterable = tuple(),
            **kwargs
    ):
        self.logger = logger
        self.base_url = galloper_url
        self.project_id = project_id
        self.build_id = build_id
        self.bucket = bucket
        # self.config_file = '{}'
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
        self.manual_run = manual_run
        self.logger_stop_words = logger_stop_words

    # def set_test_status(self, status: dict):
    #     from interceptor.utils import build_api_url
    #     import requests
    #     report_status_url = '/'.join(map(str, [
    #         self.base_url,
    #         build_api_url('backend_performance', 'report_status', skip_mode=True).lstrip('/'),
    #         self.project_id,
    #         self.report_id
    #     ]))
    #     requests.put(
    #         report_status_url,
    #         headers=self.api_headers,
    #         json={"test_status": status}
    #     )

    @property
    def env_vars(self) -> dict:
        return {
            "base_url": self.base_url,
            "token": self.token,
            "project_id": self.project_id,
            "bucket": self.bucket,
            "build_id": self.build_id,
            "report_id": self.report_id,
            "integrations": json.dumps(self.integrations),
            "exec_params": json.dumps(self.exec_params),
            "manual_run": self.manual_run,
            "debug": True,
            "logger_stop_words": json.dumps(self.logger_stop_words)
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

            job = client.run(
                POSTPROCESSOR_CONTAINER,
                stderr=True, remove=True, detach=True,
                environment=self.env_vars
            )

        return job
