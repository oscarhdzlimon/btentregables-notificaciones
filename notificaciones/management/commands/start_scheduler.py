import signal
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand

from notificaciones.tasks.scheduler_manager import initialize_scheduler


class Command(BaseCommand):
    help = 'Inicia el scheduler de tareas programadas y el servidor de desarrollo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--addr',
            type=str,
            default='0.0.0.0',
            help='Dirección IP para el servidor de desarrollo (por defecto: 0.0.0.0)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8005,
            help='Puerto para el servidor de desarrollo (por defecto: 8005)'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduler = None
        self.running = True

    def handle_sigterm(self, signum, frame):
        self.stdout.write(self.style.WARNING('\nRecibida señal de terminación. Cerrando el scheduler...'))
        if self.scheduler:
            self.scheduler.shutdown()
        self.running = False
        sys.exit(0)

    def handle(self, *args, **options):
        # Configurar el manejador de señales
        signal.signal(signal.SIGINT, self.handle_sigterm)
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        self.stdout.write('Iniciando scheduler...')
        try:
            self.scheduler = initialize_scheduler()
            self.stdout.write(self.style.SUCCESS('Scheduler iniciado exitosamente'))

            addr = options['addr']
            port = options['port']

            # Ejecutar runserver en el hilo principal
            call_command('runserver', f'{addr}:{port}', use_reloader=False)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            if self.scheduler:
                self.scheduler.shutdown()
            sys.exit(1)
