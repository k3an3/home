from celery import Celery

celery = Celery('home',
                broker='redis://',
                backend='redis://')
