#!/bin/sh

superconf -p $CPU_CORES
supervisord --configuration /etc/interceptor.conf
