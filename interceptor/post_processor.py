from os import path, environ
import json
import requests
import logging


class PostProcessor:

    def __init__(self, galloper_url, project_id, galloper_web_hook, bucket, prefix, junit=False, token=None,
                 integration=[], email_recipients=None):
        self.galloper_url = galloper_url
        self.project_id = project_id
        self.galloper_web_hook = galloper_web_hook
        self.bucket = bucket
        self.prefix = prefix
        self.config_file = '{}'
        self.junit = junit
        self.token = token
        self.integration = integration
        self.email_recipients = email_recipients

    def results_post_processing(self):
        if self.galloper_web_hook:
            if path.exists('/tmp/config.yaml'):
                with open("/tmp/config.yaml", "r") as f:
                    self.config_file = f.read()
            else:
                self.config_file = environ.get('CONFIG_FILE', '{}')

            data = {'galloper_url': self.galloper_url, 'project_id': self.project_id,
                    'config_file': json.dumps(self.config_file),
                    'bucket': self.bucket, 'prefix': self.prefix, 'junit': self.junit, 'token': self.token,
                    'integration': self.integration, "email_recipients": self.email_recipients}
            headers = {'content-type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'bearer {self.token}'

            res = requests.post(self.galloper_web_hook, json=data, headers=headers)
            logging.info(res.text)



