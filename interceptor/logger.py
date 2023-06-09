import logging
import re
from typing import Iterable, Callable

from interceptor.constants import LOKI_HOST, LOKI_PORT, LOG_LEVEL, LOG_SECRETS_REPLACER, FormatterMethods, FORMATTER_METHOD

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


def get_centry_logger(hostname: str, labels: dict = None, stop_words: Iterable = tuple()) -> logging.Logger:
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

    if stop_words:
        SecretFormatter(secrets=stop_words).patch_logger(centry_logger)

    return centry_logger


class SecretFormatter(logging.Formatter):
    REPLACER = LOG_SECRETS_REPLACER
    RESTRICTED_STOP_WORDS = {'', REPLACER}

    def __init__(self, secrets: Iterable, formatter_method: FormatterMethods = FORMATTER_METHOD):
        super().__init__()
        self.formatter_method = formatter_method
        self.secrets = set(map(str, secrets))
        self.__censor_stop_words()

    @property
    def formatter(self) -> Callable:
        try:
            return getattr(self, self.formatter_method)
        except AttributeError:
            return lambda text: text

    def __censor_stop_words(self) -> None:
        for i in self.RESTRICTED_STOP_WORDS:
            try:
                self.secrets.remove(i)
            except KeyError:
                ...

    @property
    def re_pattern(self):
        return re.compile(r'\b(?:{})\b'.format('|'.join(self.secrets)), flags=re.MULTILINE)

    def replacer_re(self, text: str) -> str:
        return re.sub(self.re_pattern, '', text)

    def replacer_iter(self, text: str) -> str:
        # replaces every occurrence
        for i in self.secrets:
            text = text.replace(i, self.REPLACER)
        return text

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        self.formatter(formatted)
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
