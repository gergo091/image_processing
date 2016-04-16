from django.conf import settings

from celery import Celery

from apps import detection_methods

celery_app = Celery(__name__)
celery_app.conf.update(**settings.CELERY_CONFIG)


@celery_app.task
def process_line_task(*args, **kwargs):
    return detection_methods.analyze(**kwargs)
