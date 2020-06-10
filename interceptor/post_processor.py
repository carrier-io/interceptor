from os import path, environ
import json
import requests


class PostProcessor:

    def __init__(self, galloper_url, project_id, galloper_web_hook, bucket, prefix, junit=False, token=None,
                 jira= False, *args, **kwargs):
        self.galloper_url = galloper_url
        self.project_id = project_id
        self.galloper_web_hook = galloper_web_hook
        self.bucket = bucket
        self.prefix = prefix
        self.config_file = '{}'
        self.junit = junit
        self.token = token
        self.jira = jira

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
                    'jira': self.jira}
            headers = {'content-type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'bearer {self.token}'

            r = requests.post(self.galloper_web_hook, json=data, headers=headers)
            print(r.text)



