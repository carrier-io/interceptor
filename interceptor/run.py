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

import docker

from os import environ
from time import sleep
from interceptor.constants import CPU_MULTIPLIER
from celery import Celery
from celery.contrib.abortable import AbortableTask

from interceptor.jobs_wrapper import JobsWrapper

REDIS_USER = environ.get('REDIS_USER', '')
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', 'password')
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = environ.get('REDIS_PORT', '6379')
REDIS_DB = environ.get('REDIS_DB', 1)


app = Celery('CarrierExecutor',
             broker=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             backend=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
             include=['celery'])


app.conf.update(timezone='UTC', result_expires=1800)


@app.task(name="tasks.execute", bind=True, acks_late=True, base=AbortableTask)
def execute_job(self, job_type, container, execution_params, redis_connection, job_name, *args, **kwargs):
    if not getattr(JobsWrapper, job_type):
        return False, "Job Type not found"
    client = docker.from_env()
    client.info()
    cid = getattr(JobsWrapper, job_type)(client, container, execution_params, job_name, redis_connection,
                                         *args, **kwargs)
    client_lowlevel = docker.APIClient(base_url='unix://var/run/docker.sock')
    last_log = []
    while cid.status != "exited":
        if self.is_aborted():
            cid.stop(timeout=60)
            return True, "Aborted"
        try:
            cid.reload()
            print(f'Container Status: {cid.status}')
            resource_usage = client_lowlevel.stats(cid.id, stream=False)
            print(f'Container {cid.id} resource usage -- '
                  f'CPU: {round(float(resource_usage["cpu_stats"]["cpu_usage"]["total_usage"])/CPU_MULTIPLIER, 2)} '
                  f'RAM: {round(float(resource_usage["memory_stats"]["usage"])/(1024*1024), 2)} Mb '
                  f'of {round(float(resource_usage["memory_stats"]["limit"])/(1024*1024), 2)} Mb')
            logs = client_lowlevel.logs(cid.id, stream=False, tail=100).decode("utf-8", errors='ignore').split('\r\n')
            for each in logs:
                if each not in last_log:
                    print(each)
            last_log = logs
        except:
            break
        sleep(10)
    return True, "Done"


def main():
    app.start()


if __name__ == '__main__':
    main()


