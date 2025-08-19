import logging
from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone
from django.utils.timezone import now
from django_apscheduler import util

from notificaciones.models import OrdenSprint, EntregableSprint, EntregableArchivo

logger = logging.getLogger(__name__)


@util.close_old_connections
def actualiza_version_entregables(**kwargs):
    fecha_ayer = timezone.now().date() - timedelta(days=1)

    orden_sprints = OrdenSprint.objects.filter(
        fecha_baja__isnull=True,
        fecha_entrega_documentos=fecha_ayer,
    ).prefetch_related(
        Prefetch(
            'entregablesprint_set',
            queryset=EntregableSprint.objects.filter(
                fecha_baja__isnull=True,
                id_entregable__id_estatus_id__lt=7,
            ).select_related('id_entregable'))
    )

    entregables = [
        entregable.id_entregable
        for sprint in orden_sprints
        for entregable in sprint.entregablesprint_set.all()
    ]

    # Procesar los archivos en lote
    for entregable in entregables:
        archivo_actual = EntregableArchivo.objects.filter(
            id_entregable=entregable,
            fecha_baja__isnull=True
        ).order_by('-major_version', '-minor_version').first()

        if not archivo_actual:
            continue

        crear_nueva_version(archivo_actual)


def crear_nueva_version(archivo_actual):
    """Crear nueva versión del archivo"""
    campos_nueva_version = {
        k: v for k, v in archivo_actual.__dict__.items()
        if k not in ('_state', 'id', 'fecha_alta', 'usuario_alta', 'major_version', 'minor_version')
    }

    return EntregableArchivo.objects.create(
        **campos_nueva_version,
        fecha_alta=now(),
        usuario_alta='JOB_ENTREGA_DOCUMENTOS',
        major_version=archivo_actual.major_version + 1,
        minor_version=0
    )
