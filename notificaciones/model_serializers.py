from rest_framework import serializers

from notificaciones.models import Notificaciones


class NotificacionesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificaciones
        fields = ['id', 'titulo', 'texto', 'fecha_alta']
        extra_kwargs = {
            'titulo': {'read_only': True},
            'texto': {'read_only': True},
            'usuario_alta': {'read_only': True},
            'fecha_alta': {'read_only': True},
            'usuario_modifica': {'read_only': True},
            'fecha_modifica': {'read_only': True}
        }
