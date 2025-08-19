from django.urls import path, include
from rest_framework.routers import DefaultRouter

from notificaciones.views import NotificacionesViewSet

router = DefaultRouter()
router.register('', NotificacionesViewSet, basename='notificaciones')

urlpatterns = [
    path('', include(router.urls)),
]
