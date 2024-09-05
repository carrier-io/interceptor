#!/usr/bin/python3
# coding=utf-8

#   Copyright 2024 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Loggers """

import logging
from typing import Iterable

from centry_logging import log  # pylint: disable=E0401
from centry_logging.internal import state  # pylint: disable=E0401
from centry_logging.formatters.secret import SecretFormatter  # pylint: disable=E0401
from centry_logging.handlers.eventnode import EventNodeLogHandler  # pylint: disable=E0401
from interceptor import constants as c


def get_interceptor_logger():
    """ Get logger for interceptor """
    return logging.getLogger("interceptor")
    # log.init(logging.INFO if c.LOG_LEVEL == "info" else logging.DEBUG, force=True)
    # #
    # try:
    #     handler = EventNodeLogHandler({
    #         "event_node": {
    #             "type": "RedisEventNode",
    #             "host": c.REDIS_HOST,
    #             "port": c.REDIS_PORT,
    #             "password": c.REDIS_PASSWORD,
    #             "event_queue": "centry_logs",
    #             "use_ssl": c.REDIS_USE_SSL,
    #         },
    #         "labels": {
    #             "application": "interceptor",
    #         },
    #     })
    #     handler.setFormatter(state.formatter)
    #     #
    #     new_logger = logging.getLogger("interceptor")
    #     new_logger.setLevel(logging.INFO if c.LOG_LEVEL == "info" else logging.DEBUG)
    #     new_logger.addHandler(handler)
    # except:  # pylint: disable=W0702
    #     log.exception("Failed to create interceptor logger, using default")
    #     new_logger = logging.getLogger("interceptor")
    # #
    # return new_logger


def get_centry_logger(hostname: str, labels: dict = None, stop_words: Iterable = tuple()) -> logging.Logger:  # pylint: disable=C0301
    """ Get logger for test """
    return logging.getLogger("centry_logger")
    # if labels is None:
    #     labels = {}
    # else:
    #     labels = labels.copy()
    # #
    # labels["hostname"] = hostname
    # #
    # try:
    #     formatter = SecretFormatter(secrets=stop_words)
    #     #
    #     handler = EventNodeLogHandler({
    #         "event_node": {
    #             "type": "RedisEventNode",
    #             "host": c.REDIS_HOST,
    #             "port": c.REDIS_PORT,
    #             "password": c.REDIS_PASSWORD,
    #             "event_queue": "centry_logs",
    #             "use_ssl": c.REDIS_USE_SSL,
    #         },
    #         "labels": labels,
    #     })
    #     handler.setFormatter(formatter)
    #     #
    #     new_logger = logging.getLogger("centry_logger")
    #     new_logger.setLevel(logging.INFO)
    #     new_logger.addHandler(handler)
    # except:  # pylint: disable=W0702
    #     log.exception("Failed setup logger for test. Used default logger")
    #     log.update_secrets(stop_words)
    #     new_logger = logging.getLogger("centry_logger")
    # #
    # return new_logger


logger = get_interceptor_logger()
