"""
async.py
~~~~~~~~

Handles running of tasks in an asynchronous fashion. Not explicitly tied to Celery. The `run` method simply must
exist here and handle the execution of whatever task is passed to it, whether or not it is handled asynchronously.
"""
from time import sleep

from apscheduler.schedulers.background import BackgroundScheduler

from settings import ASYNC_HANDLER

if ASYNC_HANDLER == 'celery':
    from celery import Celery
    from celery.security import setup_security

    setup_security(allowed_serializers=['pickle', 'json'],
                   serializer='pickle')

    queue = Celery('home',
                   broker='redis://',
                   backend='redis://',
                   serializer='pickle')

    queue.conf.update(
        CELERY_TASK_SERIALIZER='pickle',
        CELERY_ACCEPT_CONTENT=['pickle'],
    )



elif ASYNC_HANDLER == 'multiprocessing':
    from multiprocessing import Pool

    pool = Pool(processes=10)

else:
    from concurrent.futures import ThreadPoolExecutor

    executor = ThreadPoolExecutor(max_workers=10)

scheduler = BackgroundScheduler()
scheduler.start()


@queue.task
def _run(method, **kwargs) -> None:
    """
    Run the configured actions in multiple processes.
    """
    if kwargs.get('delay'):
        sleep(kwargs.pop('delay'))
    method(**kwargs)


def run(method, delay=0, **kwargs):
    if ASYNC_HANDLER == 'celery':
        _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))
    elif ASYNC_HANDLER == 'multiprocessing':
        pool.apply_async(_run, args=[method], kwargs=kwargs)
    else:
        executor.submit(_run, args=[method], kwargs=kwargs)
