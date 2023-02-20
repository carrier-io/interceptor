import logging
from multiprocessing import Queue

import logging_loki
from centry_loki import log_loki

from interceptor import constants

logger = logging.getLogger("interceptor")

if constants.LOKI_HOST:
    handler = logging_loki.LokiQueueHandler(
        Queue(-1),
        url=f"{constants.LOKI_HOST.replace('https://', 'http://')}:"
            f"{constants.LOKI_PORT}/loki/api/v1/push",
        tags={"application": "interceptor"},
        version="1",
    )

    logger.setLevel(logging.INFO if constants.LOG_LEVEL == 'info' else logging.DEBUG)
    try:
        logger.addHandler(handler)
    except ValueError as exc:
        logger.error("Can't connect to loki")


def get_centry_logger(hostname: str, labels: dict = None):
    try:
        context = {
            "url": f"{constants.LOKI_HOST.replace('https://', 'http://')}:"
                   f"{constants.LOKI_PORT}/loki/api/v1/push",
            "hostname": hostname, "labels": labels
        }
        centry_logger = log_loki.get_logger(context)
    except KeyError:
        centry_logger = logger
        centry_logger.warning("Failed setup logger for test. Used default logger")

    return centry_logger
