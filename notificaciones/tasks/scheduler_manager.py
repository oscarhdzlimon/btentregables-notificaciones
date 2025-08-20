import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django_apscheduler.models import DjangoJobExecution

from notificaciones.models import Notificaciones
from notificaciones.tasks import scheduler
from notificaciones.tasks.entrega_documentos_task import actualiza_version_entregables
from notificaciones.tasks.mail_task import send_mails
from django_apscheduler import util
from notificaciones.tasks.sla_task import actualiza_entregables_sla, actualiza_sla_atencion_clientes

logger = logging.getLogger(__name__)


def initialize_scheduler():
    if getattr(settings, 'SCHEDULER_DEFAULT', False):
        scheduler_instance = scheduler.start()

        # Programar tareas
        try:
            scheduler_instance.add_job(send_mails, 'cron', minute='*/5', hour='6-21', id='send_mails', replace_existing=True)

            scheduler_instance.add_job(actualiza_entregables_sla, 'cron', minute='0', hour='0', id='actualiza_sla', replace_existing=True)
            scheduler_instance.add_job(actualiza_sla_atencion_clientes, 'cron', minute='5', hour='0', id='actualiza_sla_atencion_clientes', replace_existing=True)
            scheduler_instance.add_job(actualiza_version_entregables, 'cron', minute='15', hour='0', id='actualiza_version_entregables', replace_existing=True)

            scheduler_instance.add_job(__limpia_datos, 'cron', day_of_week='fri', hour='6', minute='0', id='limpia_datos', replace_existing=True)
            scheduler_instance.add_job(__baja_de_notificaciones, 'cron', minute='0', hour='1', id='notificaciones_cleanup', replace_existing=True)
        except Exception as e:
            logger.error(f"Error al programar las tareas: {str(e)}")
            raise

        return scheduler_instance
    else:
        logger.warning("SCHEDULER_DEFAULT está desactivado en la configuración")
        return None


@util.close_old_connections
def __limpia_datos():
    try:
        DjangoJobExecution.objects.delete_old_job_executions(86400)
        Notificaciones.objects.filter(
            fecha_baja__isnull=False,
            fecha_baja__lte=(timezone.now() - timedelta(days=7)),
        ).delete()
    except Exception as e:
        logger.error(e)


@util.close_old_connections
def __baja_de_notificaciones():
    try:
        Notificaciones.objects.filter(
            fecha_alta__lte=(timezone.now() - timedelta(days=5)),
            fecha_baja__isnull=True
        ).update(
            fecha_baja=timezone.now(),
            usuario_baja='JOB_NOTIFICACIONES_CLEANUP',
        )
    except Exception as e:
        logger.error(e)