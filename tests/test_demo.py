import docker

from interceptor.jobs_wrapper import JobsWrapper


def test_ui_performance_task():
    client = docker.from_env()
    client.info()

    execution_params = {
        "REMOTE_PORT": "4444",
        "LISTENER_PORT": "9999",
        "mounts": [{"/tmp/reports": "/tmp/reports"},
                   {"/home/sergey/SynologyDrive/Github/observer/tests/data": "/data"}],
        "cmd": "-f /data/webmail.side -r html -fp 100 -si 400 -tl 500 -g False"
    }

    job_name = "test_ui_perf"

    container = JobsWrapper.ui_performance(client, container="spirogov/observer:0.3",
                                           execution_params=execution_params, job_name=job_name)

    print(container.id)