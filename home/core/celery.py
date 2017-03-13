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


@queue.task(serializer='pickle')
def _run(method, **kwargs) -> None:
    """
    Run the configured actions in multiple processes.
    """
    method(**kwargs)


def run(method, delay=0, **kwargs):
    _run.apply_async(args=[method], kwargs=kwargs, countdown=float(delay))
