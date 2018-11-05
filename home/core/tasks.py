"""
tasks.py
~~~~~~~~

Handles running of tasks in an asynchronous fashion. Not explicitly tied to Celery. The `run` method simply must
exist here and handle the execution of whatever task is passed to it, whether or not it is handled asynchronously.
"""
from multiprocessing import Process
from time import sleep
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from celery import Celery
from celery.security import setup_security
from celery.utils.log import get_task_logger
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal

from home.settings import ASYNC_MODE, SENTRY_URL

setup_security(allowed_serializers=['pickle', 'json'],
               serializer='pickle')

queue = Celery('home',
               broker='redis://',
               backend='redis://',
               serializer='pickle')

queue.conf.update(
    CELERY_TASK_SERIALIZER='pickle',
    CELERY_ACCEPT_CONTENT=['pickle', 'json'],
    CELERY_TASK_SOFT_TIME_LIMIT=30,
)

try:
    import gevent

    from apscheduler.schedulers.gevent import GeventScheduler

    scheduler = GeventScheduler()
except ImportError:
    scheduler = BackgroundScheduler()
scheduler.start()
logger = get_task_logger(__name__)


@queue.task
def _run(method, **kwargs) -> None:
    """
    Run the configured actions in multiple processes.
    """
    logger.info('Running {} on {} with config: {}'.format(method.__name__,
                                                          method.__self__,
                                                          kwargs
                                                          ))
    method(**kwargs)


def run(method: Callable, delay: float = 0, **kwargs):
    if ASYNC_MODE == 'celery':
        return _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))
    else:
        return multiprocessing_run(method, delay, **kwargs)


def multiprocessing_run(target: Callable, delay: float = 0, **kwargs):
    if delay:
        sleep(delay)
    Process(target=target, kwargs=kwargs).start()


if SENTRY_URL:
    client = Client(SENTRY_URL)

    # register a custom filter to filter out duplicate logs
    register_logger_signal(client)

    # The register_logger_signal function can also take an optional argument
    # `loglevel` which is the level used for the handler created.
    # Defaults to `logging.ERROR`
    import logging

    register_logger_signal(client, loglevel=logging.INFO)

    # hook into the Celery error handler
    register_signal(client)

    # The register_signal function can also take an optional argument
    # `ignore_expected` which causes exception classes specified in Task.throws
    # to be ignored
    register_signal(client, ignore_expected=True)
