import docker

from interceptor import constants as c


class JobsWrapper(object):
    @staticmethod
    def dast(container, execution_params, job_name, redis_connection):
        client = docker.from_env()
        required_keys = ['host', 'port', 'protocol', 'test_type']
        if not all(k in execution_params for k in required_keys):
            return False, "Missing required params (%s)" % ",".join(required_keys)
        if not [container] in [k.tags for k in client.images.list()]:
            return False, "Please specify proper tag of security container e.g. getcarrier/dast:latest"
        host = execution_params.get('host')
        port = execution_params.get('port')
        protocol = execution_params.get('protocol')
        project = execution_params.get('project', job_name)
        environment = execution_params.get('environment', "default")
        client.containers.run(container, name=job_name,
                              nano_cpus=c.CONTAINER_CPU_QUOTA, mem_limit=c.CONTAINER_MEMORY_QUOTA,
                              command=f"-s {execution_params['test_type']}",
                              environment={"host": host, "port": port,
                                           "protocol": protocol, "project_name": project,
                                           "environment": environment,
                                           "redis_connection": redis_connection},
                              oom_kill_disable=True, remove=True)
        return True, "Done"

    @staticmethod
    def sast(container, execution_params, job_name, redis_connection):
        pass