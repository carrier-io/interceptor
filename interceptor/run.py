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
import signal
from os import environ
from time import sleep
from traceback import format_exc

import boto3
import requests
from arbiter import Minion

from interceptor import constants as c
from interceptor.containers_backend import KubernetesClient, DockerClient, Job, KubernetesJob
from interceptor.jobs_wrapper import JobsWrapper
from interceptor.lambda_executor import LambdaExecutor
from interceptor.logger import logger, get_centry_logger
from interceptor.post_processor import PostProcessor

RABBIT_USER = environ.get('RABBIT_USER', 'user')
RABBIT_PASSWORD = environ.get('RABBIT_PASSWORD', 'password')
RABBIT_HOST = environ.get('RABBIT_HOST', 'localhost')
RABBIT_PORT = environ.get('RABBIT_PORT', '5672')
QUEUE_NAME = environ.get('QUEUE_NAME', "default")
CPU_CORES = environ.get('CPU_CORES', 2)
VHOST = environ.get('VHOST', 'carrier')
TOKEN = environ.get('TOKEN', '')

app = Minion(host=RABBIT_HOST, port=RABBIT_PORT,
             user=RABBIT_USER, password=RABBIT_PASSWORD, queue=QUEUE_NAME, vhost=VHOST)

stop_task = False


def sigterm_handler(signal, frame):
    global stop_task
    stop_task = True


signal.signal(signal.SIGTERM, sigterm_handler)


@app.task(name="terminate_ec2_instances")
def terminate_ec2_instances(
        aws_access_key_id, aws_secret_access_key, region_name, fleet_id, launch_template_id
):
    try:
        ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key_id,
                           aws_secret_access_key=aws_secret_access_key,
                           region_name=region_name)
        response = ec2.delete_fleets(
            FleetIds=[
                fleet_id,
            ],
            TerminateInstances=True
        )
        logger.info(response)
        response = ec2.delete_launch_template(
            LaunchTemplateId=launch_template_id
        )
        logger.info(response)
        return "Done"
    except Exception:
        logger.error(format_exc())
        logger.info("Failed to terminate AWS ec2 instances")
        return "Failed"


@app.task(name="post_process")
def post_process(
        galloper_url, project_id, galloper_web_hook, report_id, bucket, prefix,
        build_id, token=None, integration=[]
):
    centry_logger = get_centry_logger({
        "build_id": build_id,
        "project_id": project_id,
        "report_id": report_id,
    })
    centry_logger.info("Start post processing")
    try:
        PostProcessor(galloper_url, project_id, galloper_web_hook, report_id, bucket,
                      prefix, centry_logger, token,
                      integration).results_post_processing()
    except Exception:
        centry_logger.info("Failed to run postprocessor")


@app.task(name="browsertime")
def browsertime(
        galloper_url, project_id, token, bucket, filename, url, view='1920x1080',
        tests='1', headers=None, browser="", *args, **kwargs
):
    try:
        if not headers:
            headers = {}
        client = DockerClient(logger)
        env_vars = {"galloper_url": galloper_url, "project_id": project_id, "token": token,
                    "bucket": bucket,
                    "filename": filename, "view": view, "tests": tests}
        cmd = url
        if headers:
            cmd += " -H "
            for key, value in headers.items():
                if key.strip().lower() not in c.STRIP_HEADERS:
                    cmd += f'"{key.strip()}:{value.strip()}" '
        if browser:
            cmd += f" -b {browser}"

        job = getattr(JobsWrapper, 'browsertime')(client, c.BROWSERTIME_CONTAINER, env_vars,
                                                  cmd)
        while job.status != "exited":
            logger.info(f"Executing: {c.BROWSERTIME_CONTAINER}")
            logger.info(f"Execution params: {cmd}")
            logger.info(f"Container {job.id} status {job.status}")
            try:
                job.reload()
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


@app.task(name="execute_kuber")
def execute_kuber(job_type, container, execution_params, job_name, kubernetes_settings):
    centry_logger = get_centry_logger(execution_params)

    if not getattr(JobsWrapper, job_type):
        centry_logger.error("Job Type not found")
        return

    client = KubernetesClient(**kubernetes_settings, logger=centry_logger)
    try:
        job: KubernetesJob = getattr(JobsWrapper, job_type)(client, container,
                                                            execution_params, job_name)
    except Exception as exc:
        centry_logger.error(exc)
        return
    last_logs = []
    while not job.is_finished():
        sleep(10)
        global stop_task
        if stop_task:
            stop_task = False
            job.stop_job()
            return
        try:
            job.log_status(last_logs)
        except Exception as exc:
            centry_logger.warning(f"FETCHING LOGS FAILED {exc}")
    return "Done"


@app.task(name="execute")
def execute_job(job_type, container, execution_params, job_name):
    centry_logger = get_centry_logger(execution_params)

    if not getattr(JobsWrapper, job_type):
        centry_logger.error("Job Type not found")
        return

    client = DockerClient(logger=centry_logger)
    client.info()
    centry_logger.info(f"Executing: {job_type} on {container} with name {job_name}")
    centry_logger.info(f"Execution params: {execution_params}")
    try:
        job: Job = getattr(JobsWrapper, job_type)(client, container, execution_params,
                                                  job_name)
    except:
        centry_logger.error(f"Failed to run docker container {container}")
        return
    last_logs = []
    while not job.is_finished():
        sleep(10)
        global stop_task
        if stop_task:
            stop_task = False
            job.stop_job()
            centry_logger.info(f"Aborted: {job_type} on {container} with name {job_name}")
            return
        try:
            job.log_status(last_logs)
        except:
            break
    return


def main():
    if QUEUE_NAME != "__internal":
        url = f"{c.LOKI_HOST}/api/v1/projects/rabbitmq/{VHOST}"
        data = {"name": QUEUE_NAME}
        headers = {'content-type': 'application/json'}
        if TOKEN:
            headers['Authorization'] = f'bearer {TOKEN}'
        requests.post(url, json=data, headers=headers)
    app.run(workers=int(CPU_CORES))


if __name__ == '__main__':
    main()
