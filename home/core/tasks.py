"""
tasks.py
~~~~~~~~

Handles running of tasks in an asynchronous fashion. Not explicitly tied to Celery. The `run` method simply must
exist here and handle the execution of whatever task is passed to it, whether or not it is handled asynchronously.
"""
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from celery import Celery
from celery.utils.log import get_task_logger

from home.settings import ASYNC_MODE, SENTRY_URL, BROKER_PATH, BACKEND_PATH, MAX_THREADS, MAX_PROCESSES
try:
    from sentry_sdk import init

    if SENTRY_URL:
        init(SENTRY_URL)
except ImportError:
    pass

queue = Celery('home',
               broker=BROKER_PATH,
               backend=BACKEND_PATH,
               )

queue.conf.update(
    CELERY_TASK_SOFT_TIME_LIMIT=30,
)

try:
    import gevent

    from apscheduler.schedulers.gevent import GeventScheduler

    scheduler = GeventScheduler()
    thread_runner = gevent.spawn
except ImportError:
    scheduler = BackgroundScheduler()
    executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
    thread_runner = executor.submit
scheduler.start()
logger = get_task_logger(__name__)

if ASYNC_MODE == 'multiprocessing':
    executor = ProcessPoolExecutor(max_workers=MAX_PROCESSES)


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


def run(method: Callable, delay: float = 0, thread: bool = False, **kwargs):
    if ASYNC_MODE == 'celery':
        return _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))
    elif thread:
        return thread_run(method, delay, **kwargs)
    else:
        return multiprocessing_run(method, delay, **kwargs)


def thread_run(target: Callable, delay: float = 0, **kwargs):
    if delay:
        sleep(delay)
    return thread_runner(target, **kwargs)


def multiprocessing_run(target: Callable, delay: float = 0, **kwargs):
    if delay:
        sleep(delay)
    return executor.submit(target, **kwargs)
