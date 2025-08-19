from django.utils.timezone import now
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notificaciones.model_serializers import NotificacionesModelSerializer
from notificaciones.models import Notificaciones, Usuario, UsuarioOrdenServicio


class NotificacionesViewSet(viewsets.ModelViewSet):
    queryset = Notificaciones.objects.filter(fecha_baja__isnull=True).order_by('-id')
    serializer_class = NotificacionesModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.method != 'GET':
            return super().get_queryset()
            
        req_user = Usuario.objects.get(id=self.request.user.id, fecha_baja__isnull=True)
        user_notifications = Notificaciones.objects.filter(
            fecha_baja__isnull=True,
            id_usuario=req_user.id
        )

        if req_user.is_externo == 0:
            role_notifications = Notificaciones.objects.filter(
                fecha_baja__isnull=True,
                id_rol=req_user.id_rol,
                id_orden__id__in=UsuarioOrdenServicio.objects.filter(
                    id_orden__fecha_baja__isnull=True,
                    id_usuario=req_user,
                ).values_list('id_orden', flat=True)
            )
        else:
            role_notifications = Notificaciones.objects.filter(
                fecha_baja__isnull=True,
                id_rol=req_user.id_rol,
                id_orden__id__in=UsuarioOrdenServicio.objects.filter(
                    id_orden__fecha_baja__isnull=True,
                    id_orden__id_proyecto__id_contrato__id_cliente=req_user.id_cliente,
                ).values_list('id_orden', flat=True)
            )

        return user_notifications.union(role_notifications).order_by('-id')

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.usuario_baja = request.user.id if request.user else None
        instance.fecha_baja = now()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, 400)
