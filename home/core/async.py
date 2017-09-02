"""
async.py
~~~~~~~~

Handles running of tasks in an asynchronous fashion. Not explicitly tied to Celery. The `run` method simply must
exist here and handle the execution of whatever task is passed to it, whether or not it is handled asynchronously.
"""
from multiprocessing import Process
from time import sleep

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.gevent import GeventScheduler
from celery import Celery
from celery.security import setup_security
from celery.utils.log import get_task_logger
from typing import Callable

setup_security(allowed_serializers=['pickle', 'json'],
               serializer='pickle')

queue = Celery('home',
               broker='redis://',
               backend='redis://',
               serializer='pickle')

queue.conf.update(
    CELERY_TASK_SERIALIZER='pickle',
    CELERY_ACCEPT_CONTENT=['pickle', 'json'],
)

try:
    import gevent

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


def run(method, delay=0, **kwargs):
    return _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))


def multiprocessing_run(target: Callable, delay: float = 0, kwargs: dict = {}):
    if delay:
        sleep(delay)
    Process(target=target, kwargs=kwargs).start()
