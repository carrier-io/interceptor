from os import environ
from celery import Celery
from interceptor.jobs_wrapper import JobsWrapper

REDIS_USER = environ.get('REDIS_USER', '')
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', 'password')
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = environ.get('REDIS_PORT', '6379')


app = Celery('CarrierExecutor',
             broker=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1',
             backend=f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/1',
             include=['celery'])


app.conf.update(timezone='UTC', result_expires=1800)


@app.task(name="tasks.execute", acks_late=True)
def execute_job(job_type, container, execution_params, job_name):
    redis_connection = f'redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{job_name.replace(" ", "")}'
    if not getattr(JobsWrapper, job_type):
        return False, "Job Type not found"
    return getattr(JobsWrapper, job_type)(container, execution_params, job_name, redis_connection)


def main():
    app.start()


if __name__ == '__main__':
    main()


