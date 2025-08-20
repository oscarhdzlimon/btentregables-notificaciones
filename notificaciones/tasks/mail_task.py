import logging

from django.template.loader import render_to_string
from django.utils.timezone import now
from django_apscheduler import util

from notificaciones.models import Notificaciones, Usuario, UsuarioOrdenServicio, InfoBlue
from notificaciones.utils import send_mail_html_attachments

logger = logging.getLogger(__name__)


@util.close_old_connections
def send_mails(**kwargs):
    mails = Notificaciones.objects.filter(fecha_modifica__isnull=True)

    for mail in mails:
        try:
            logger.debug('Sending mail %s', mail)
            if mail.id_usuario:
                __mail_usuario(mail)
            elif mail.id_rol:
                __mail_rol(mail)
        except Exception as e:
            logger.error('Error sending mail %s', e)
        finally:
            __mail_notificado(mail)


def __images_by_template(template_name):
    image_template_map = {
        'mail/reset-passwd.html': [ 'logo-pm.png', 'passwd-lock.png' ]
    }

    return image_template_map.get(template_name, ['logo-pm.png'])


def __mail_notificado(mail: Notificaciones):
    try:
        Notificaciones.objects.filter(id=mail.id).update(usuario_modifica='JOB_SEND_MAILS', fecha_modifica=now())
    except Exception as e:
        logger.error('Error sending mail %s', e)


def __mail_usuario(mail: Notificaciones):
    body = render_to_string(mail.template, mail.datos)
    send_mail_html_attachments(to=[mail.id_usuario.email], subject=mail.titulo, body_html=body,
                               image_names=__images_by_template(mail.template),
                               attachments=__get_attachments(mail))


def __mail_rol(mail: Notificaciones):
    destinatarios = list(
        Usuario.objects.filter(
            id__in=UsuarioOrdenServicio.objects.filter(
                id_orden=mail.id_orden,
                id_usuario__id_rol_id__in=[mail.id_rol],
                id_usuario__is_externo=mail.externo,
            ).values_list('id_usuario', flat=True)
        ).values_list('email', flat=True)
    )

    if destinatarios.__len__() > 0:
        body = render_to_string(mail.template, mail.datos)
        send_mail_html_attachments(to=destinatarios, subject=mail.titulo, body_html=body,
                                   image_names=__images_by_template(mail.template),
                                   attachments=__get_attachments(mail))


def __get_attachments(mail: Notificaciones):
    if mail.template == 'mail/nueva-orden.html':
        return [entregable.path.path for entregable in InfoBlue.get_entregables_iniciales(mail.id_cliente)]

    return None