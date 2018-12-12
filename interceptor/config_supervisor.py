import argparse

interceptor_conf = """[supervisord]

[program:worker]
command=celery -A interceptor.run worker -l info -c%s --max-tasks-per-child 1 -f /var/log/interceptor.log
autostart=true
autorestart=true
stopsignal=QUIT
stopwaitsecs=20
stopasgroup=true"""


def arg_parse():
    parser = argparse.ArgumentParser(description='Supervisord Config Creator')
    parser.add_argument('-p', '--procs', type=int, default=4, help="specify amount of cores on server")
    return parser.parse_args()


def main():
    args = arg_parse()
    with open('/etc/interceptor.conf', 'w') as f:
        f.write(interceptor_conf % args.procs)