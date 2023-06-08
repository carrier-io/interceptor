import logging
from typing import Iterable

from interceptor.constants import LOKI_HOST, LOKI_PORT, LOG_LEVEL

logger = logging.getLogger("interceptor")


if LOKI_HOST:
    from multiprocessing import Queue
    from logging_loki import LokiQueueHandler
    handler = LokiQueueHandler(
        Queue(-1),
        url=f"{LOKI_HOST.replace('https://', 'http://')}:"
            f"{LOKI_PORT}/loki/api/v1/push",
        tags={"application": "interceptor"},
        version="1",
    )

    logger.setLevel(logging.INFO if LOG_LEVEL == 'info' else logging.DEBUG)
    try:
        logger.addHandler(handler)
    except ValueError as exc:
        logger.error("Can't connect to loki")


def get_centry_logger(hostname: str, labels: dict = None) -> logging.Logger:
    from centry_loki import log_loki
    try:
        context = {
            "url": f"{LOKI_HOST.replace('https://', 'http://')}:"
                   f"{LOKI_PORT}/loki/api/v1/push",
            "hostname": hostname, "labels": labels
        }
        centry_logger = log_loki.get_logger(context)
    except KeyError:
        centry_logger = logger
        centry_logger.warning("Failed setup logger for test. Used default logger")

    return centry_logger


class SecretFormatter(logging.Formatter):
    REPLACER = '***'

    def __init__(self, secrets: Iterable):
        super().__init__()
        self.secrets = set(map(str, secrets))

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        for i in self.secrets:
            formatted = formatted.replace(i, self.REPLACER)
        return formatted

    def patch_logger(self, logger_: logging.Logger) -> None:
        for handler_ in logger_.handlers:
            if isinstance(handler_.formatter, self.__class__):
                handler_.formatter.secrets.update(self.secrets)
            else:
                handler_.setFormatter(self)


# if __name__ == '__main__':
#     import sys
#
#     stop_words2 = ['stop', 'words', ]
#     stop_words = ['secret', '1', 'WARNING']
#
#     logger.setLevel(logging.DEBUG)
#     test_handler = logging.StreamHandler(stream=sys.stdout)
#     # test_handler.setFormatter(SecretFormatter())
#     logger.addHandler(test_handler)
#
#     secret_formatter = SecretFormatter(stop_words)
#     secret_formatter.patch_logger(logger)
#
#     for i in range(2):
#         if i == 1:
#             print('=' * 20)
#             SecretFormatter(stop_words2).patch_logger(logger)
#         logger.info('this is a simple log')
#         logger.warning('this is a simple warning')
#
#         logger.info('this is a stop word')
#         logger.warning('this is a secret warning')
#
#         logger.info('this is a stop words secret')
#         logger.warning('this is a stopwordssecret')
#         logger.info('this is a 43212341')
