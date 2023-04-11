import pytest
import requests_mock
import tests.utils.constants as c
from interceptor.post_processor import PostProcessor

galloper_url = "https://example.com"
galloper_web_hook = "hook"
project_id = 1
token = "test"


def test_results_post_processing():
    with requests_mock.Mocker() as mock:
        post_processor = PostProcessor(galloper_url=galloper_url, project_id=project_id,
                                       galloper_web_hook=galloper_web_hook, bucket="test", prefix="test")
        # todo: check if url is correct
        mock.get(f"{galloper_url}/api/v1/task/{project_id}/{galloper_web_hook}?exec=True", json=c.task_info)
        mock.register_uri(requests_mock.POST, c.docker_volume_url, status_code=204, json={"Id": "1"})
        mock.get(c.galloper_get_artifact, content=open("tests/utils/test.zip", "rb").read(), status_code=200)
        mock.register_uri(requests_mock.POST, c.docker_create_url, status_code=204, json={"Id": "1"})
        mock.get(c.docker_get_container_info_url, json={"Id": "1", "HostConfig": {"LogConfig": {"Type": "default"}}})
        mock.post(c.docker_start_url, json={"Id": "1"})
        mock.post(c.docker_wait_url, json={"StatusCode": 0})
        mock.delete(c.docker_delete_url)
        # todo: check if url is correct
        mock.post(f"{galloper_url}/api/v1/task/{project_id}/results")
        post_processor.results_post_processing()
        assert mock.call_count == 10
