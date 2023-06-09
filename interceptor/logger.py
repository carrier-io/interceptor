import logging
import re
from typing import Iterable, Union

from interceptor.constants import LOKI_HOST, LOKI_PORT, LOG_LEVEL, \
    LOG_SECRETS_REPLACER, FormatterMethods, FORMATTER_METHOD

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

    def __init__(self, secrets: Iterable, formatter_method: Union[FormatterMethods, str] = FORMATTER_METHOD):
        super().__init__()
        self.formatter_method = formatter_method
        self.secrets = set(map(str, secrets))
        self.__censor_stop_words()

        try:
            self.formatter = getattr(self, self.formatter_method)
        except AttributeError:
            logging.warning('Formatter method %s not found. Falling back to %s', self.formatter_method,
                            FormatterMethods.RE)
            self.formatter = self.replacer_re

    def __censor_stop_words(self) -> None:
        for i in self.RESTRICTED_STOP_WORDS:
            try:
                self.secrets.remove(i)
            except KeyError:
                ...

    @property
    def re_pattern(self):
        return re.compile(r'\b(?:{})\b'.format('|'.join(self.secrets)))

    def replacer_re(self, text: str) -> str:
        # replaces only separate words
        return re.sub(self.re_pattern, self.REPLACER, text)

    def replacer_iter(self, text: str) -> str:
        # replaces every occurrence
        for i in self.secrets:
            print('\t', text, '<->', i)
            text = text.replace(i, self.REPLACER)
        return text

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return self.formatter(formatted)

    def patch_logger(self, logger_: logging.Logger) -> None:
        for handler_ in logger_.handlers:
            if isinstance(handler_.formatter, self.__class__):
                self.secrets.update(handler_.formatter.secrets)
            handler_.setFormatter(self)
