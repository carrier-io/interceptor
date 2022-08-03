from os import path, environ
import json
import requests
import logging
from interceptor.lambda_executor import LambdaExecutor


class PostProcessor:

    def __init__(self, galloper_url, project_id, galloper_web_hook, report_id, bucket, prefix, token=None,
                 integration=[]):
        self.galloper_url = galloper_url
        self.project_id = project_id
        self.galloper_web_hook = galloper_web_hook
        self.bucket = bucket
        self.prefix = prefix
        self.config_file = '{}'
        self.token = token
        self.integration = integration
        self.report_id = report_id

    def results_post_processing(self):
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
            endpoint = f"api/v1/tasks/task/{self.project_id}/" \
                       f"{self.galloper_web_hook.replace(self.galloper_url + '/task/', '')}?exec=True"
            headers = {'Authorization': f'bearer {self.token}', 'content-type': 'application/json'}
            task = requests.get(f"{self.galloper_url}/{endpoint}", headers=headers).json()

            LambdaExecutor(task, event, self.galloper_url, self.token).execute_lambda()



