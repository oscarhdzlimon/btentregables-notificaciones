import logging
import os
from email.mime.image import MIMEImage

import environ
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)
env = environ.Env()


def send_mail_html(to, subject, body_html):
    try:
        mail = EmailMultiAlternatives(subject=subject, to=to)
        mail.attach_alternative(body_html, 'text/html')
        __send_mail(mail)
    except Exception as e:
        logger.error(e)


def send_mail_html_attachments(to, subject, body_html, image_names, attachments=None):
    try:
        mail = EmailMultiAlternatives(subject=subject, to=to)
        mail.attach_alternative(body_html, 'text/html')

        for image_name in image_names:
            image_path = os.path.join('static', 'images', image_name)
            with open(image_path, 'rb') as img:
                image = MIMEImage(img.read())
                image.add_header('Content-ID', '<{}>'.format(image_name))
                mail.attach(image)

        if attachments:
            for attachment in attachments:
                mail.attach_file(attachment)

        __send_mail(mail)
    except Exception as e:
        logger.error(e)


def __send_mail(mail: EmailMultiAlternatives):
    try:
        email_host = env('EMAIL_HOST', default=None)

        if not email_host or email_host == 'logger':
            logger.info(f'Sending email: {mail.subject} to {mail.to}')
            logger.debug(f'Body: {mail.alternatives[0][0]}')
        else:
            mail.send()
    except Exception as e:
        logger.error(e)
