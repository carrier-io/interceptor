# interceptor
Task manager based on celery worker

Should be installed on any machine or VM that planned to be used as a jobs executor

### Execution

```
docker run -d --rm -v /var/run/docker.sock:/var/run/docker.sock  \
      -e CPU_CORES=$CPU_CORES -e REDIS_PASSWORD=$REDIS_PASSWORD  \
      -e REDIS_HOST=$FULLHOST \
      getcarrier/interceptor:latest
```

Interceptor need docker.sock to be mounted as it going to provision new containers on host os

`CPU_CORES` - is an amount of cores you'd like to dedicated for tasks execution

`REDIS_HOST` - address of your redis service (just a name or IP, w/o port) localhost is default
 
`REDIS_PORT` - port of your redis service. 6379 is default

`REDIS_USER` - is a username to your Redis server. empty string is default

`REDIS_PASSWORD` - is a password to your Redis server. password is default


It require redis to be running somewhere.
simple container can be used for that
```
docker run -d -p 6379:6379 --name carrier-redis \
	   redis:5.0.2 redis-server --requirepass $REDIS_PASSWORD
```


