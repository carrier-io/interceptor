#!/bin/bash

superconf
supervisord --configuration "${SUPERVISOR_CONF_PATH:-/etc/interceptor.conf}"
