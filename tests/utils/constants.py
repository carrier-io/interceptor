docker_create_url = "http+docker://localhost/v1.35/containers/create"

docker_get_container_info_url = "http+docker://localhost/v1.35/containers/1/json"

docker_start_url = "http+docker://localhost/v1.35/containers/1/start"

docker_volume_url = "http+docker://localhost/v1.35/volumes/create"

docker_wait_url = "http+docker://localhost/v1.35/containers/1/wait"

docker_delete_url = "http+docker://localhost/v1.35/containers/1?v=False&link=False&force=False"

task_info = {"id": "1", "project_id": 1, "task_id": "1", "zippath": "tasks/test.zip", "task_name": "test",
             "task_handler": "lambda.handler", "runtime": "Python 3.7", "webhook": "/task/test", "last_run": "1",
             "status": "activated", "token": "test", "func_args": {"test": 1}, "env_vars": '{"test": 1}', "callback": ""}

galloper_get_artifact = "https://example.com//api/v1/artifacts/1/tasks/test.zip"
