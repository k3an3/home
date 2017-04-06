"""
async.py
~~~~~~~~

Handles running of tasks in an asynchronous fashion. Not explicitly tied to Celery. The `run` method simply must
exist here and handle the execution of whatever task is passed to it, whether or not it is handled asynchronously.
"""
from apscheduler.schedulers.background import BackgroundScheduler
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
    CELERY_ACCEPT_CONTENT=['pickle', 'json'],
)
scheduler = BackgroundScheduler()
scheduler.start()


@queue.task
def _run(method, **kwargs) -> None:
    """
    Run the configured actions in multiple processes.
    """
    method(**kwargs)


def run(method, delay=0, **kwargs):
    return _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))
