import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)


def start():
    scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())
    scheduler.add_jobstore(DjangoJobStore(), "default")

    try:
        # Inicio del scheduler
        scheduler.start()
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    return scheduler
