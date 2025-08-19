import logging
from datetime import datetime, timedelta
from django.db import connection
from django.utils.timezone import now
from django_apscheduler import util
import json

logger = logging.getLogger(__name__)

@util.close_old_connections
def actualiza_entregables_sla(**kwargs):
    logger.info("Iniciando actualización de SLA...")

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT "FEC_INHABIL"
            FROM "EPMC_DIAS_INHABILES"
            WHERE "STP_BAJA_REGISTRO" IS NULL
        ''')
        dias_inhabiles = set(row[0] for row in cursor.fetchall())
        logger.info(f" Días inhabilitados cargados: {len(dias_inhabiles)}")

        cursor.execute('''
            SELECT 
                e."ID_ENTREGABLE", 
                e."FEC_INICIO", 
                e."ID_INFOBLUE", 
                e."NOM_ENTREGABLE", 
                u."ID_USUARIO", 
                u."ID_ROL", 
                u."REF_EMAIL",
                o."ID_ORDEN", 
                o."REF_NOMBRE" AS "NOM_ORDEN"
            FROM "EPMT_ENTREGABLES" e
            JOIN "EPMT_USUARIOS" u ON e."ID_USUARIO_RESPONSABLE" = u."ID_USUARIO"
            JOIN "EPMT_ORDEN_SERVICIO" o ON e."ID_ORDEN" = o."ID_ORDEN"
            WHERE 
                e."ID_ESTATUS" < 7
                AND e."STP_BAJA_REGISTRO" IS NULL
                AND u."STP_BAJA_REGISTRO" IS NULL
                AND u."IND_ACTIVO" = 1
        ''')

        entregables = cursor.fetchall()
        logger.info(f" Entregables a procesar: {len(entregables)}")

        entregables_actualizados = []

        for (
            id_entregable, fec_inicio, id_infoblue, nombre_entregable,
            id_usuario, id_rol, email_responsable,
            id_orden, nombre_orden
        ) in entregables:

            if fec_inicio is None:
                color = None
            else:
                hoy = datetime.now().date()
                dias_transcurridos = 0
                dia_actual = fec_inicio

                while dia_actual <= hoy:
                    if dia_actual.weekday() < 5 and dia_actual not in dias_inhabiles:
                        dias_transcurridos += 1
                    dia_actual += timedelta(days=1)

                logger.debug(f" Entregable {id_entregable} - Días hábiles transcurridos: {dias_transcurridos}")

                cursor.execute('''
                    SELECT "NUM_SLA_VERDE", "NUM_SLA_AMARILLO", "NUM_SLA_ROJO"
                    FROM "EPMC_INFOBLUE"
                    WHERE "ID_INFOBLUE" = %s
                ''', [id_infoblue])
                sla = cursor.fetchone()

                if sla:
                    sla_verde, sla_amarillo, sla_rojo = sla

                    if dias_transcurridos <= sla_verde:
                        color = 'VERDE'
                    elif dias_transcurridos <= sla_amarillo:
                        color = 'AMARILLO'
                    elif dias_transcurridos >= sla_rojo:
                        color = 'ROJO'
                    else:
                        color = None
                else:
                    logger.warning(f" SLA no encontrado para ID_INFOBLUE {id_infoblue}")
                    color = None

            if color:
                cursor.execute('''
                    UPDATE "EPMT_ENTREGABLES"
                    SET "REF_COLOR_SLA" = %s,
                        "STP_MODIFICA_REGISTRO" = %s,
                        "CVE_USUARIO_MODIFICA" = %s
                    WHERE "ID_ENTREGABLE" = %s
                ''', [color, now(), "JOB_SLA", id_entregable])
                entregables_actualizados.append(id_entregable)
                logger.info(f" Entregable {id_entregable} actualizado a SLA: {color}")

                if color != "VERDE":
                    cursor.execute('''
                        SELECT est."NOM_ESTATUS"
                        FROM "EPMT_ENTREGABLES" ent
                        JOIN "EPMC_ESTATUS_ENTREGABLE" est ON ent."ID_ESTATUS" = est."ID_ESTATUS"
                        WHERE ent."ID_ENTREGABLE" = %s
                    ''', [id_entregable])
                    resultado = cursor.fetchone()
                    nombre_estatus = resultado[0] if resultado else "SIN ESTATUS"

                    titulo = f"Un entregable llegó al estado: {nombre_estatus.upper()}"
                    texto = f"Nombre del entregable: {nombre_entregable}"
                    template = "mail/actualiza-entregables-sla.html"
                    datos_json = json.dumps({
                        "titulo": titulo,
                        "id_entregable": id_entregable,
                        "nombre_entregable": nombre_entregable,
                        "nombre_orden": nombre_orden,
                        "dias_atraso": dias_transcurridos
                    })

                    cursor.execute('''
                        INSERT INTO "EPMT_NOTIFICACIONES" (
                            "ID_USUARIO", "ID_ROL", "REF_TITULO", "REF_TEXTO", 
                            "REF_TEMPLATE", "REF_DATOS", "CVE_USUARIO_ALTA", 
                            "STP_ALTA_REGISTRO", "ID_ORDEN"
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', [
                        id_usuario,
                        id_rol,
                        titulo,
                        texto,
                        template,
                        datos_json,
                        "JOB_SLA",
                        now(),
                        id_orden
                    ])
                    logger.info(f" Notificación insertada para entregable {id_entregable}.")

    logger.info(f" SLA actualizado para {len(entregables_actualizados)} entregables.")


@util.close_old_connections
def actualiza_sla_atencion_clientes(**kwargs):
    logger.info("Iniciando actualización de SLA de atención a clientes...")

    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT e."FEC_INHABIL"
            FROM "EPMC_DIAS_INHABILES" e
            WHERE e."STP_BAJA_REGISTRO" IS NULL
        ''')
        dias_inhabiles = set(row[0] for row in cursor.fetchall())
        logger.info(f"Días inhabilitados cargados: {len(dias_inhabiles)}")

        cursor.execute('''
            SELECT e."ID_ENTREGABLE", e."REF_COLOR_SLA", e."NOM_ENTREGABLE", c."ID_CLIENTE", o."ID_ORDEN"
            FROM "EPMT_ENTREGABLES" e
            JOIN "EPMT_ORDEN_SERVICIO" o ON e."ID_ORDEN" = o."ID_ORDEN"
            JOIN "EPMT_PROYECTOS" p ON o."ID_PROYECTO" = p."ID_PROYECTO"
            JOIN "EPMT_CONTRATOS" c ON p."ID_CONTRATO" = c."ID_CONTRATO"
            WHERE e."ID_ESTATUS" = 3 AND e."STP_BAJA_REGISTRO" IS NULL
        ''')

        entregables = cursor.fetchall()
        logger.info(f"Total de entregables encontrados: {len(entregables)}")

        if not entregables:
            logger.warning("No se encontraron entregables para actualizar.")
            return

        entregables_actualizados = []

        for id_entregable, color_sla, nombre_entregable, id_cliente, id_orden in entregables:
            logger.info(f"Procesando entregable ID: {id_entregable}, ID_CLIENTE: {id_cliente}")

            cursor.execute('''
                SELECT "ID_USUARIO", "ID_ROL"
                FROM "EPMT_USUARIOS"
                WHERE "ID_CLIENTE" = %s AND "IND_ACTIVO" = 1 AND "STP_BAJA_REGISTRO" IS NULL
                LIMIT 1
            ''', [id_cliente])

            usuario = cursor.fetchone()
            id_usuario = usuario[0] if usuario else None
            id_rol = usuario[1] if usuario else None

            if not id_usuario:
                logger.warning(
                    f"No se encontró un usuario activo para el cliente {id_cliente}, se omitirá la notificación.")
                continue

            cursor.execute('''
                SELECT "NUM_SLA_VERDE", "NUM_SLA_AMARILLO", "NUM_SLA_ROJO"
                FROM "EPMC_CLIENTE_SLA"
                WHERE "ID_CLIENTE" = %s
                ORDER BY "ID_CLIENTE_SLA" ASC
                LIMIT 1
            ''', [id_cliente])

            sla = cursor.fetchone()

            if not sla:
                logger.info(f"No se encontró SLA para el cliente {id_cliente}, buscando SLA por defecto.")
                cursor.execute('''
                    SELECT "NUM_SLA_VERDE", "NUM_SLA_AMARILLO", "NUM_SLA_ROJO"
                    FROM "EPMC_CLIENTE_SLA"
                    WHERE "ID_CLIENTE_SLA" = 1
                ''')
                sla = cursor.fetchone()

            if not sla:
                logger.error(f"No se encontró SLA por defecto. Saltando entregable {id_entregable}.")
                continue

            sla_verde, sla_amarillo, sla_rojo = sla
            dias_transcurridos = 0
            dia_actual = datetime.now().date()

            cursor.execute('''SELECT "FEC_INICIO" FROM "EPMT_ENTREGABLES" WHERE "ID_ENTREGABLE" = %s''',
                           [id_entregable])
            fec_inicio = cursor.fetchone()[0]

            if not fec_inicio:
                logger.warning(
                    f"El campo 'fec_inicio' es None para el entregable {id_entregable}, se omitirá el cálculo del SLA.")
                continue

            while fec_inicio <= dia_actual:
                if fec_inicio.weekday() < 5 and fec_inicio not in dias_inhabiles:
                    dias_transcurridos += 1
                fec_inicio += timedelta(days=1)

            logger.debug(f"Entregable {id_entregable} - Días hábiles transcurridos: {dias_transcurridos}")

            if dias_transcurridos <= sla_verde:
                nuevo_color_sla = 'VERDE'
            elif dias_transcurridos <= sla_amarillo:
                nuevo_color_sla = 'AMARILLO'
            elif dias_transcurridos >= sla_rojo:
                nuevo_color_sla = 'ROJO'
            else:
                nuevo_color_sla = None

            logger.info(f"Nuevo color SLA calculado para entregable {id_entregable}: {nuevo_color_sla}")

            if nuevo_color_sla and nuevo_color_sla != 'VERDE':
                cursor.execute('''
                    SELECT "ID_ARCHIVO"
                    FROM "EPMT_ENTREGABLE_ARCHIVO"
                    WHERE "ID_ENTREGABLE" = %s
                    ORDER BY "CVE_MAJOR_VERSION" DESC, "STP_ALTA_REGISTRO" DESC
                    LIMIT 1
                ''', [id_entregable])

                archivo = cursor.fetchone()

                if archivo:
                    id_entregable_archivo = archivo[0]
                    cursor.execute('''
                        UPDATE "EPMT_ENTREGABLE_ARCHIVO"
                        SET "REF_SLA_CLIENTE" = %s, "STP_MODIFICA_REGISTRO" = %s, "CVE_USUARIO_MODIFICA" = %s
                        WHERE "ID_ARCHIVO" = %s
                    ''', [nuevo_color_sla, datetime.now(), "JOB_SLA_CLIENTE", id_entregable_archivo])

                    entregables_actualizados.append(id_entregable)
                    logger.info(f"SLA actualizado para entregable {id_entregable}: {nuevo_color_sla}")
                else:
                    logger.warning(f"No se encontró archivo para el entregable {id_entregable}, no se actualizó SLA.")

                cursor.execute('''
                    SELECT "REF_NOMBRE"
                    FROM "EPMT_ORDEN_SERVICIO"
                    WHERE "ID_ORDEN" = %s
                ''', [id_orden])

                orden = cursor.fetchone()
                nombre_orden = orden[0] if orden else "Orden no encontrada"

                cursor.execute('''
                    SELECT "NOM_ESTATUS"
                    FROM "EPMC_ESTATUS_ENTREGABLE"
                    WHERE "ID_ESTATUS" = (SELECT "ID_ESTATUS" FROM "EPMT_ENTREGABLES" WHERE "ID_ENTREGABLE" = %s)
                ''', [id_entregable])

                estatus = cursor.fetchone()
                nombre_estatus = estatus[0] if estatus else "SIN ESTATUS"
                titulo = f"Un entregable llegó al estado: {nombre_estatus.upper()}"

                datos_json = json.dumps({
                    "titulo": titulo,
                    "id_entregable": id_entregable,
                    "nombre_entregable": nombre_entregable,
                    "nombre_orden": nombre_orden,
                    "dias_atraso": dias_transcurridos
                })

                cursor.execute('''
                    INSERT INTO "EPMT_NOTIFICACIONES" (
                        "ID_USUARIO", "ID_ROL", "REF_TITULO", "REF_TEXTO", "REF_TEMPLATE", "REF_DATOS", 
                        "CVE_USUARIO_ALTA", "STP_ALTA_REGISTRO", "ID_ORDEN"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', [
                    id_usuario,
                    id_rol,
                    titulo,
                    f"Nombre del entregable: {nombre_entregable}",
                    "mail/actualizacion-sla-clientes.html",
                    datos_json,
                    "JOB_SLA_CLIENTE",
                    datetime.now(),
                    id_orden
                ])
                logger.info(f"Notificación insertada para entregable {id_entregable}.")
            else:
                logger.info(
                    f"No se inserta notificación para el entregable {id_entregable} porque el color SLA es VERDE.")

        logger.info(f"SLA de atención a clientes actualizado para {len(entregables_actualizados)} entregables.")

