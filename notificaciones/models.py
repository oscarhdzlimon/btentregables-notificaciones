import os

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        if 'id_rol' in extra_fields and isinstance(extra_fields['id_rol'], Rol):
            extra_fields['id_rol'] = extra_fields['id_rol']

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Obtén la instancia del rol admin y asigna su ID
        try:
            admin_role = Rol.objects.get(id=1)
            extra_fields['id_rol'] = admin_role
        except Rol.DoesNotExist:
            raise ValueError('The Admin role must exist in the Rol table')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class AuditModel(models.Model):
    usuario_alta = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_ALTA')
    fecha_alta = models.DateTimeField(null=True, db_column='STP_ALTA_REGISTRO')
    usuario_modifica = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_MODIFICA')
    fecha_modifica = models.DateTimeField(null=True, db_column='STP_MODIFICA_REGISTRO')
    usuario_baja = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_BAJA')
    fecha_baja = models.DateTimeField(null=True, db_column='STP_BAJA_REGISTRO')

    class Meta:
        abstract = True


class Rol(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ROL')
    rol = models.CharField(max_length=255, null=True, db_column='REF_ROL')
    rol_breve = models.CharField(max_length=255, null=True, db_column='REF_ROL_BREVE')
    activo = models.IntegerField(default=1, db_column='IND_ACTIVO')

    def __str__(self):
        return f"{self.id} - {self.rol}"

    class Meta:
        db_table = 'EPMC_ROLES'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        constraints = [
            models.UniqueConstraint(fields=['rol'], name='EPMT_ROLES_ROL_UNIQUE')
        ]


class Empresa(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_EMPRESA')
    nombre = models.CharField(max_length=255, null=True, db_column='NOM_EMPRESA')

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMC_EMPRESA'
        verbose_name = 'Empresa ligada'
        verbose_name_plural = 'Empresas ligadas'


class Cliente(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_CLIENTE')
    id_empresa_ligada = models.ForeignKey(Empresa, on_delete=models.RESTRICT, db_column='ID_EMPRESA_LIGADA')
    nombre = models.CharField(max_length=255, db_column='NOM_CLIENTE')
    nombre_corto = models.CharField(max_length=30, db_column='NOM_CORTO')
    rfc = models.CharField(max_length=255, unique=True, db_column='CVE_RFC')
    razon_social = models.CharField(max_length=255, db_column='REF_RAZON_SOCIAL')
    giro = models.CharField(max_length=255, db_column='REF_GIRO')
    direccion = models.CharField(max_length=255, db_column='REF_DIRECCION')

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMT_CLIENTES'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        constraints = [
            models.UniqueConstraint(fields=['rfc'], name='EPMX_BT_PK_RFC')
        ]


class Usuario(AbstractBaseUser):
    id = models.AutoField(primary_key=True, db_column='ID_USUARIO')
    id_rol = models.ForeignKey(Rol, on_delete=models.RESTRICT, db_column='ID_ROL')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, null=True, db_column='ID_CLIENTE')
    is_active = models.IntegerField(default=1, db_column='IND_ACTIVO')
    is_externo = models.IntegerField(default=0, db_column='IND_EXTERNO')
    cargo = models.CharField(max_length=255, null=True, db_column='REF_CARGO')
    nombre = models.CharField(max_length=255, null=True, db_column='REF_NOMBRE')
    primer_apellido = models.CharField(max_length=255, null=True, db_column='REF_PRIMER_APELLIDO')
    segundo_apellido = models.CharField(max_length=255, null=True, db_column='REF_SEGUNDO_APELLIDO')
    email = models.EmailField(unique=True, db_column='REF_EMAIL')
    password = models.CharField(max_length=255, db_column='REF_CONTRASENA')
    token_verificacion = models.CharField(max_length=60, null=True, db_column='REF_TOKEN_VERIFICACION')
    codigo_verificacion = models.CharField(max_length=10, null=True, db_column='REF_CODIGO_VERIFICACION')
    fecha_codigo = models.DateTimeField(blank=True, null=True, db_column='STP_CODIGO_VERIFICACION')
    usuario_alta = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_ALTA')
    fecha_alta = models.DateTimeField(null=True, db_column='STP_ALTA_REGISTRO')
    usuario_modifica = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_MODIFICA')
    fecha_modifica = models.DateTimeField(null=True, db_column='STP_MODIFICA_REGISTRO')
    usuario_baja = models.CharField(max_length=255, null=True, db_column='CVE_USUARIO_BAJA')
    fecha_baja = models.DateTimeField(null=True, db_column='STP_BAJA_REGISTRO')
    last_login = models.DateTimeField(blank=True, null=True, db_column='STP_LAST_LOGIN', editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = 'EPMT_USUARIOS'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        constraints = [
            models.UniqueConstraint(fields=['email'], name='EPMT_USUARIOS_EMAIL_KEY')
        ]

    @property
    def nombre_completo(self):
        if self.nombre or self.primer_apellido:
            return ' '.join(usu for usu in [self.nombre, self.primer_apellido, self.segundo_apellido] if usu)

        return None

    def __str__(self):
        return f"[{self.id}] {self.nombre_completo}"


class ClienteSLA(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_CLIENTE_SLA')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, db_column='ID_CLIENTE')
    sla_verde = models.IntegerField(default=0, db_column='NUM_SLA_VERDE')
    sla_amarillo = models.IntegerField(default=0, db_column='NUM_SLA_AMARILLO')
    sla_rojo = models.IntegerField(default=0, db_column='NUM_SLA_ROJO')

    def __str__(self):
        return f"{self.id} - {self.id_cliente} - [V: {self.sla_verde}, A: {self.sla_amarillo}, R: {self.sla_rojo}]"

    class Meta:
        db_table = 'EPMC_CLIENTE_SLA'
        verbose_name = 'Cliente SLA'
        verbose_name_plural = 'Cliente SLAs'
        constraints = [
            models.UniqueConstraint(fields=['id_cliente'], name='EPMC_CLIENTE_SLA_ID_UNIQUE')
        ]


class Contrato(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_CONTRATO')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, db_column='ID_CLIENTE')
    clave_contrato = models.CharField(max_length=255, db_column='CVE_CONTRATO')
    nombre_contrato = models.CharField(max_length=255, db_column='NOM_CONTRATO')

    def __str__(self):
        return f"{self.id} - {self.nombre_contrato}"

    class Meta:
        db_table = 'EPMT_CONTRATOS'
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'


class Proyecto(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_PROYECTO')
    id_contrato = models.ForeignKey(Contrato, null=True, on_delete=models.RESTRICT, db_column='ID_CONTRATO')
    clave_proyecto = models.CharField(null=True, max_length=255, db_column='CVE_PROYECTO')
    nombre_proyecto = models.CharField(max_length=255, db_column='NOM_PROYECTO')

    def __str__(self):
        return f"{self.id} - {self.nombre_proyecto}"

    class Meta:
        db_table = 'EPMT_PROYECTOS'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'


class EstatusEntregable(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ESTATUS')
    nombre = models.CharField(max_length=50, db_column='NOM_ESTATUS')
    descripcion = models.CharField(max_length=255, null=True, db_column='REF_DESCRIPCION')

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMC_ESTATUS_ENTREGABLE'
        verbose_name = 'Estatus de Entregable'
        verbose_name_plural = 'Estatus de Entregables'


class Etapa(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ETAPA')
    nombre = models.CharField(max_length=50, db_column='NOM_ETAPA')
    descripcion = models.CharField(max_length=300, null=True, db_column='REF_DESCRIPCION')

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMC_ETAPAS'
        verbose_name = 'Etapa'
        verbose_name_plural = 'Etapas'


class OrdenServicio(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ORDEN')
    id_proyecto = models.ForeignKey(Proyecto, on_delete=models.RESTRICT, db_column='ID_PROYECTO')
    id_responsable = models.ForeignKey(Usuario, on_delete=models.RESTRICT, null=True, db_column='ID_USUARIO_RESPONSABLE')
    num_semanas_duracion = models.IntegerField(null=True, db_column='NUM_SEMANAS_DURACION')
    nombre = models.CharField(max_length=255, db_column='REF_NOMBRE')
    nombre_corto = models.CharField(max_length=255, db_column='REF_NOMBRE_CORTO')
    fecha_inicio = models.DateField(null=True, db_column='FEC_INICIO')
    fecha_fin = models.DateField(null=True, db_column='FEC_FIN')

    @property
    def etapa_actual(self):
        from datetime import date
        today = date.today()

        propuesta = InfoBlue.get_id_propuesta_by_cliente(self.id_proyecto.id_contrato.id_cliente.id)
        if propuesta:
            propuesta_entregable = Entregable.objects.filter(id_infoblue__id=propuesta.id,
                                                             id_orden=self.id,
                                                             id_estatus__id__lt=7)
            if propuesta_entregable.exists():
                return 'Propuesta de solución pendiente'

        orden_etapa = OrdenEtapa.objects.filter(
            id_orden=self,
            fecha_inicio__lte=today,
            fecha_fin__gte=today,
            fecha_baja__isnull=True
        ).first()

        if orden_etapa:
            return orden_etapa.id_etapa.nombre

        return None

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMT_ORDEN_SERVICIO'
        verbose_name = 'Orden de Servicio'
        verbose_name_plural = 'Ordenes de Servicio'


class OrdenEtapa(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ORDEN_ETAPA')
    id_orden = models.ForeignKey(OrdenServicio, on_delete=models.RESTRICT, db_column='ID_ORDEN')
    id_etapa = models.ForeignKey(Etapa, on_delete=models.RESTRICT, db_column='ID_ETAPA')
    num_semanas_duracion = models.IntegerField(default=2, db_column='NUM_SEMANAS_DURACION')
    fecha_inicio = models.DateField(null=True, db_column='FEC_INICIO')
    fecha_fin = models.DateField(null=True, db_column='FEC_FIN')

    def __str__(self):
        return f"{self.id} - [{self.id_orden}] - [{self.id_etapa}]"

    class Meta:
        db_table = 'EPMT_ORDEN_ETAPA'
        verbose_name = 'Orden Etapa'
        verbose_name_plural = 'Ordenes Etapas'
        constraints = [
            models.UniqueConstraint(fields=['id_orden', 'id_etapa'], name='EPMT_ORDEN_ETAPA_UNIQUE')
        ]


class OrdenSprint(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_SPRINT')
    id_orden_etapa = models.ForeignKey(OrdenEtapa, on_delete=models.RESTRICT, db_column='ID_ORDEN_ETAPA')
    num_semanas_duracion = models.IntegerField(default=2, null=True, blank=True, db_column='NUM_SEMANAS_DURACION')
    fecha_inicio = models.DateField(null=True, blank=True, db_column='FEC_INICIO')
    fecha_fin = models.DateField(null=True, blank=True, db_column='FEC_FIN')
    fecha_entrega_documentos = models.DateField(null=True, blank=True, db_column='FEC_ENTREGA_DOCUMENTOS')

    class Meta:
        db_table = "EPMT_ORDEN_SPRINTS"
        verbose_name = 'Orden Sprint'
        verbose_name_plural = 'Orden Sprints'

    def __str__(self):
        return f"Sprint {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"


class InfoBlue(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_INFOBLUE')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, db_column='ID_CLIENTE')
    etapa = models.IntegerField(default=0, db_column='CVE_ETAPA')
    clave = models.CharField(default='', max_length=255, db_column='CVE_INFOBLUE')
    nombre = models.CharField(default='', max_length=255, db_column='NOM_INFOBLUE')
    entregable_inicial = models.IntegerField(default=0, db_column='IND_ENTREGABLE_INICIAL')
    path = models.FileField(max_length=500, db_column='REF_PATH')
    sla_verde = models.IntegerField(default=0, db_column='NUM_SLA_VERDE')
    sla_amarillo = models.IntegerField(default=0, db_column='NUM_SLA_AMARILLO')
    sla_rojo = models.IntegerField(default=0, db_column='NUM_SLA_ROJO')

    @staticmethod
    def get_id_propuesta_by_cliente(id_cliente):
        propuesta_solucion = InfoBlue.objects.filter(id_cliente__id=id_cliente, entregable_inicial=1).order_by('id').first()
        return propuesta_solucion if propuesta_solucion else InfoBlue.objects.filter(id_cliente=1, entregable_inicial=1).order_by('id').first()

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMC_INFOBLUE'
        verbose_name = 'InfoBlue'
        verbose_name_plural = 'InfoBlues'


class Entregable(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ENTREGABLE')
    id_orden = models.ForeignKey(OrdenServicio, on_delete=models.RESTRICT, db_column='ID_ORDEN')
    id_responsable = models.ForeignKey(Usuario, on_delete=models.RESTRICT, null=True, db_column='ID_USUARIO_RESPONSABLE')
    id_estatus = models.ForeignKey(EstatusEntregable, on_delete=models.RESTRICT, default=1, db_column='ID_ESTATUS')
    id_infoblue = models.ForeignKey(InfoBlue, on_delete=models.RESTRICT, null=True, db_column='ID_INFOBLUE')
    color_sla = models.CharField(max_length=20, default='VERDE', db_column='REF_COLOR_SLA')
    nombre = models.CharField(max_length=300, db_column='NOM_ENTREGABLE')
    fecha_inicio = models.DateField(null=True, db_column='FEC_INICIO')
    fecha_fin = models.DateField(null=True, db_column='FEC_FIN')
    fecha_entrega = models.DateField(null=True, db_column='FEC_ENTREGA')
    fecha_vobo = models.DateField(null=True, db_column='FEC_VOBO')

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    class Meta:
        db_table = 'EPMT_ENTREGABLES'
        verbose_name = 'Entregable'
        verbose_name_plural = 'Entregables'

    @property
    def usuarios_relacionados(self):
        return Usuario.objects.filter(
            id__in=UsuarioOrdenServicio.objects.filter(
                id_orden__in=OrdenServicio.objects.filter(
                    id__in=OrdenEtapa.objects.filter(
                        id=self.id_orden.id
                    ).values_list('id_orden', flat=True)
                ).values_list('id', flat=True)
            ).values_list('id_usuario', flat=True),
            fecha_baja__isnull=True
        )

    @property
    def nombre_responsable(self):
        if self.id_responsable:
            return self.id_responsable.nombre_completo

        return None

    @property
    def version_actual(self):
        version_actual = EntregableArchivo.objects.filter(
            id_entregable__id=self.id,
            fecha_baja__isnull=True
        ).order_by('-major_version', '-minor_version').first()

        if version_actual:
            return f'v{version_actual.major_version}.{version_actual.minor_version}'
        return None

    @property
    def extension(self):
        version_actual = EntregableArchivo.objects.filter(
            id_entregable__id=self.id,
            fecha_baja__isnull=True
        ).order_by('-major_version', '-minor_version').first()

        if version_actual:
            return version_actual.extension
        return None


class EntregableSprint(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ENTREGABLE_SPRINT')
    id_entregable = models.ForeignKey(Entregable, on_delete=models.RESTRICT, db_column='ID_ENTREGABLE')
    id_sprint = models.ForeignKey(OrdenSprint, on_delete=models.RESTRICT, db_column='ID_SPRINT')

    class Meta:
        db_table = 'EPMT_ENTREGABLE_SPRINT'
        verbose_name = 'Entregable sprint'
        verbose_name_plural = 'Entregables sprints'


class EntregableFlujo(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ENTREGABLE_FLUJO')
    id_infoblue = models.IntegerField(null=True, db_column='ID_INFOBLUE')
    id_estatus_inicial = models.ForeignKey(EstatusEntregable, on_delete=models.RESTRICT, related_name='estatus_inicial', db_column='ID_ESTATUS_INICIAL')
    id_estatus_final = models.ForeignKey(EstatusEntregable, on_delete=models.RESTRICT, related_name='estatus_final', db_column='ID_ESTATUS_FINAL')
    accion = models.CharField(max_length=10, db_column='REF_ACCION')

    def __str__(self):
        return f'Infoblue: {self.id_infoblue} | [{self.id_estatus_inicial}] => ({self.accion}) => [{self.id_estatus_final}]'

    class Meta:
        db_table = 'EPMC_ENTREGABLES_FLUJOS'
        unique_together = (('id_estatus_inicial', 'id_estatus_final', 'accion', 'id_infoblue'),)
        verbose_name = 'Entregable Flujo'
        verbose_name_plural = 'Entregables Flujos'


class EntregableEstatusHist(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ESTATUS_ENT_HIST')
    id_entregable = models.ForeignKey(Entregable, on_delete=models.RESTRICT, db_column='ID_ENTREGABLE')
    estatus_ant = models.ForeignKey(EstatusEntregable, on_delete=models.RESTRICT, related_name='estatus_ant', db_column='ID_ESTATUS_ANT')
    estatus = models.ForeignKey(EstatusEntregable, on_delete=models.RESTRICT, related_name='estatus', db_column='ID_ESTATUS')

    def __str__(self):
        return f'{self.id} | [{self.estatus_ant} -> {self.estatus}]'

    class Meta:
        db_table = 'EPMT_ENTREGABLE_ESTATUS_HIST'
        verbose_name = 'Entregable Estatus'
        verbose_name_plural = 'Entregables Estatus'


class UsuarioOrdenServicio(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_USUARIO_ORDEN')
    id_usuario = models.ForeignKey(Usuario, on_delete=models.RESTRICT, db_column='ID_USUARIO')
    id_orden = models.ForeignKey(OrdenServicio, on_delete=models.RESTRICT, db_column='ID_ORDEN')

    def __str__(self):
        return f'{self.id_usuario} - {self.id_orden}'

    class Meta:
        db_table = 'EPMT_USUARIO_ORDEN_SERVICIO'
        verbose_name = 'Usuario Orden de Servicio'
        verbose_name_plural = 'Usuarios Ordenes de Servicio'
        constraints = [
            models.UniqueConstraint(fields=['id_usuario', 'id_orden'], name='EPMT_USUARIO_ORDEN_UNIQUE'),
        ]


class EntregableArchivo(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_ARCHIVO')
    id_entregable = models.ForeignKey(Entregable, on_delete=models.RESTRICT, db_column='ID_ENTREGABLE')
    major_version = models.IntegerField(default=0, db_column='CVE_MAJOR_VERSION')
    minor_version = models.IntegerField(db_column='CVE_MINOR_VERSION')
    nombre = models.CharField(max_length=500, db_column='REF_NOMBRE')
    extension = models.CharField(max_length=500, db_column='REF_EXTENSION')
    comentario = models.CharField(max_length=999, db_column='REF_COMENTARIO')
    path = models.FileField(max_length=700, db_column='REF_PATH')
    file_hash = models.CharField(max_length=300, db_column='REF_HASH')
    sla_actual = models.CharField(max_length=20, db_column='REF_SLA_ACTUAL')
    sla_cliente = models.CharField(max_length=20, db_column='REF_SLA_CLIENTE')

    def __str__(self):
        return f"[{self.id_entregable.id}] {self.id} - {self.nombre} - v{self.major_version}.{self.minor_version}"

    @property
    def nombre_sin_extension(self):
        return os.path.splitext(self.nombre)[0]

    @property
    def nombre_version(self):
        return f'v{self.major_version}.{self.minor_version}'

    @property
    def full_name(self):
        return f'{self.id_entregable.id_infoblue.clave}_{self.id_entregable.id_infoblue.nombre}_{self.nombre_version}.{self.extension}'

    @staticmethod
    def obtener_siguiente_version(id_entregable):
        ultima_version = (EntregableArchivo.objects
                          .filter(id_entregable__id=id_entregable, fecha_baja__isnull=True)
                          .order_by('-major_version', '-minor_version').first())
        if ultima_version:
            return [ultima_version.major_version, ultima_version.minor_version + 1]
        return [0, 1]

    class Meta:
        db_table = 'EPMT_ENTREGABLE_ARCHIVO'
        verbose_name = 'Entregable Archivo'
        verbose_name_plural = 'Entregables Archivos'


class TipoSprint(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_TIPO_SPRINT')
    nombre = models.CharField(max_length=30, db_column='NOM_SPRINT')
    descripcion = models.CharField(max_length=300, db_column='REF_DESCRIPCION')

    class Meta:
        db_table = 'EPMC_TIPO_SPRINT'
        verbose_name = 'Tipo de Sprint'
        verbose_name_plural = 'Tipos de Sprint'

    def __str__(self):
        return f"{self.id} - {self.nombre}"


class DetalleSprint(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_DETALLE_SPRINT')
    id_sprint = models.ForeignKey(OrdenSprint, null=True, on_delete=models.RESTRICT, db_column='ID_SPRINT')
    id_orden_etapa = models.ForeignKey(OrdenEtapa, null=True, on_delete=models.RESTRICT, db_column='ID_ORDEN_ETAPA')
    id_tipo_sprint = models.ForeignKey(TipoSprint, on_delete=models.RESTRICT, db_column='ID_TIPO_SPRINT')
    fecha_inicio = models.DateField(null=True, db_column='FEC_INICIO')
    fecha_fin = models.DateField(null=True, db_column='FEC_FIN')
    num_semanas_duracion = models.IntegerField(default=2, db_column='NUM_SEMANAS_DURACION')

    class Meta:
        db_table = 'EPMT_DETALLE_SPRINT'
        verbose_name = 'Detalle de Sprint'
        verbose_name_plural = 'Detalles de Sprint'

    def __str__(self):
        return f"{self.id} - {self.id_tipo_sprint} - {self.id_sprint}"


class Notificaciones(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_NOTIFICACION')
    id_usuario = models.ForeignKey(Usuario, null=True, on_delete=models.RESTRICT, db_column='ID_USUARIO')
    id_rol = models.ForeignKey(Rol, null=True, on_delete=models.RESTRICT, db_column='ID_ROL')
    id_orden = models.ForeignKey(OrdenServicio, null=True, on_delete=models.RESTRICT, db_column='ID_ORDEN')
    externo = models.IntegerField(default=0, db_column='IND_EXTERNO')
    titulo = models.CharField(max_length=150, db_column='REF_TITULO')
    texto = models.CharField(max_length=500, db_column='REF_TEXTO')
    template = models.CharField(max_length=50, db_column='REF_TEMPLATE')
    datos = models.JSONField(max_length=150, db_column='REF_DATOS')

    class Meta:
        db_table = 'EPMT_NOTIFICACIONES'
        verbose_name = 'Notificacion'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"{self.id} - {self.titulo}"


class DiaInhabil(AuditModel):
    id = models.AutoField(primary_key=True, db_column='ID_DIA_INHABIL')
    fecha = models.DateField(null=False, db_column='FEC_DIA_INHABIL')

    class Meta:
        db_table = 'EPMC_DIAS_INHABILES'
        verbose_name = 'Dia Inhabil'
        verbose_name_plural = 'Dias Inhabiles'

    def __str__(self):
        return f"{self.fecha}"
