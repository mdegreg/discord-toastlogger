import logging
import sys


MIN_LOGGING_LEVEL = logging.DEBUG


LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def init_logging(out=sys.stdout, err=sys.stderr, level=logging.WARNING):
    logger = logging.getLogger()
    logger.setLevel(level)
