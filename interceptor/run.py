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
import signal
import logging_loki
from multiprocessing import Queue
from arbiter import Minion
import logging
from os import environ
from time import sleep
from interceptor import constants as c
from traceback import format_exc
from interceptor.jobs_wrapper import JobsWrapper
from interceptor.post_processor import PostProcessor
from interceptor.lambda_executor import LambdaExecutor
from json import dumps

RABBIT_USER = environ.get('RABBIT_USER', 'user')
RABBIT_PASSWORD = environ.get('RABBIT_PASSWORD', 'password')
RABBIT_HOST = environ.get('RABBIT_HOST', 'localhost')
RABBIT_PORT = environ.get('RABBIT_PORT', '5672')
QUEUE_NAME = environ.get('QUEUE_NAME', "default")
CPU_CORES = environ.get('CPU_CORES', 2)

app = Minion(host=RABBIT_HOST, port=RABBIT_PORT,
             user=RABBIT_USER, password=RABBIT_PASSWORD, queue=QUEUE_NAME)

logger = logging.getLogger("interceptor")


if c.LOKI_HOST:
    handler = logging_loki.LokiQueueHandler(
        Queue(-1),
        url=f"{c.LOKI_HOST.replace('https://', 'http://')}:{c.LOKI_PORT}/loki/api/v1/push",
        tags={"application": "interceptor"},
        version="1",
    )

    logger.setLevel(logging.INFO if c.LOG_LEVEL == 'info' else logging.DEBUG)
    logger.addHandler(handler)


stop_task = False


def sigterm_handler(signal, frame):
    global stop_task
    stop_task = True


signal.signal(signal.SIGTERM, sigterm_handler)


@app.task(name="post_process")
def post_process(galloper_url, project_id, galloper_web_hook, bucket, prefix, junit=False, token=None, integration=[],
                 email_recipients=None):
    try:
        PostProcessor(galloper_url, project_id, galloper_web_hook, bucket,
                      prefix, junit, token, integration, email_recipients).results_post_processing()
        return "Done"
    except Exception:
        logger.error(format_exc())
        logger.info("Failed to run post processor")
        return "Failed"


@app.task(name="browsertime")
def browsertime(container, galloper_url, project_id, token, bucket, filename, url, view='1920x1080', tests='1',
                headers={}, browser=""):

    try:
        client = docker.from_env()
        env_vars = {"galloper_url": galloper_url, "project_id": project_id, "token": token, "bucket": bucket,
                    "filename": filename, "view": view, "tests": tests}
        cmd = url
        if headers:
            cmd += " -H "
            for key, value in headers.items():
                cmd += f'{key.replace(" ", "")}:{value.replace(" ", "")} '
        if browser:
            cmd += f" -b {browser}"

        cid = getattr(JobsWrapper, 'browsertime')(client, container, env_vars, cmd)
        while cid.status != "exited":
            logger.info(f"Executing: {container}")
            logger.info(f"Execution params: {cmd}")
            logger.info(f"Container {cid.id} status {cid.status}")
            try:
                cid.reload()
            except:
                break
            sleep(10)
        return "Done"
    except Exception:
        logger.error(format_exc())
        logger.info("Failed to run browsertime task")
        return "Failed"


@app.task(name="execute_lambda")
def execute_lambda(task, event, galloper_url, token):
    try:
        LambdaExecutor(task, event, galloper_url, token).execute_lambda()
        return "Done"
    except Exception:
        logger.error(format_exc())
        logger.info(f"Failed to execute {task['task_name']} lambda")
        return "Failed"


@app.task(name="execute")
def execute_job(job_type, container, execution_params, job_name):
    if not getattr(JobsWrapper, job_type):
        return False, "Job Type not found"
    client = docker.from_env()
    client.info()
    logger.info(f"Executing: {job_type} on {container} with name {job_name}")
    logger.info(f"Execution params: {execution_params}")
    try:
        cid = getattr(JobsWrapper, job_type)(client, container, execution_params, job_name)
    except:
        return f"Failed to run docker container {container}"
    logger.info(f"Container {cid.id} status {cid.status}")
    client_lowlevel = docker.APIClient(base_url='unix://var/run/docker.sock')
    last_log = []
    while cid.status != "exited":
        global stop_task
        if stop_task:
            stop_task = False
            cid.stop(timeout=60)
            logger.info(f"Aborted: {job_type} on {container} with name {job_name}")
            exit(0)
        try:
            cid.reload()
            logger.info(f'Container Status: {cid.status}')
            resource_usage = client_lowlevel.stats(cid.id, stream=False)
            logger.info(f'Container {cid.id} resource usage -- '
                        f'CPU: {round(float(resource_usage["cpu_stats"]["cpu_usage"]["total_usage"]) / c.CPU_MULTIPLIER, 2)} '
                        f'RAM: {round(float(resource_usage["memory_stats"]["usage"]) / (1024 * 1024), 2)} Mb '
                        f'of {round(float(resource_usage["memory_stats"]["limit"]) / (1024 * 1024), 2)} Mb')
            logs = client_lowlevel.logs(cid.id, stream=False, tail=100).decode("utf-8", errors='ignore').split('\r\n')
            for each in logs:
                if each not in last_log:
                    logging.info(each)
            last_log = logs
        except:
            break
        sleep(10)
    return "Done"


def main():
    app.run(workers=int(CPU_CORES))


if __name__ == '__main__':
    main()


