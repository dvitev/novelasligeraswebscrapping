import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recopilarnovelasdjango.settings")

app = Celery("recopilarnovelas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(('app',))