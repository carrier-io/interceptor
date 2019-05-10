#!/bin/sh

superconf -p $CPU_CORES
supervisord --configuration /etc/interceptor.conf
sleep 5
tail -f /var/log/interceptor.log