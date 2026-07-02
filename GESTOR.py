"""
GESTOR.py — Modelo y lógica de negocio del Mini CRM de servicio al cliente.
Reglas:
  - Un cliente puede tener muchas PQRS.
  - Una PQRS NO puede crearse si el cliente no existe.
  - Toda creación genera log tipo_evento='CREACION'.
  - Todo cambio de estado genera log tipo_evento='CAMBIO_ESTADO'.
  - Todo comentario genera log tipo_evento='COMENTARIO'.
  - Nunca eliminar una PQRS al atender.
"""

from abc import ABC, abstractmethod
from datetime import datetime

from database import BaseDatosPQRS

TIPOS_PQRS = {"Peticion", "Queja", "Reclamo", "Sugerencia"}
ESTADOS_VALIDOS = {"Abierta", "En_Proceso", "Escalada", "Cerrada"}


# ── Generación de radicados persistentes ────────────────────────────────────

def _nuevo_radicado(db: BaseDatosPQRS) -> str:
    """Genera un radicado secuencial basado en el último registrado en BD."""
    ultimo = db.obtener_ultimo_radicado()
    if ultimo is None:
        return "PQRS-0001"
    try:
        num = int(ultimo.split("-")[1]) + 1
    except (IndexError, ValueError):
        num = 1
    return f"PQRS-{num:04d}"


# ── OBSERVER ────────────────────────────────────────────────────────────────

class Observador(ABC):
    @abstractmethod
    def actualizar(self, mensaje: str): pass


class NotificadorCliente(Observador):
    def actualizar(self, mensaje: str):
        print(f"Cliente: {mensaje}")


class NotificadorAgente(Observador):
    def actualizar(self, mensaje: str):
        print(f"Agente: {mensaje}")


# ── STRATEGY ────────────────────────────────────────────────────────────────

class EstrategiaPrioridad(ABC):
    @abstractmethod
    def calcular_prioridad(self, tipo: str) -> int: pass


class PrioridadPorTipo(EstrategiaPrioridad):
    MAPA = {"Reclamo": 1, "Queja": 2, "Peticion": 3, "Sugerencia": 4}

    def calcular_prioridad(self, tipo: str) -> int:
        return self.MAPA.get(tipo, 5)


# ── MODELO ──────────────────────────────────────────────────────────────────

class PQRS(ABC):
    def __init__(self, radicado: str, descripcion: str,
                 asunto: str = "", cliente_id: int = 0,
                 estado: str = "Abierta", prioridad: int = 4,
                 canal_ingreso: str = "",
                 fecha_creacion: str | None = None):
        self.radicado = radicado
        self.descripcion = descripcion
        self.asunto = asunto
        self.cliente_id = cliente_id
        self.estado = estado
        self.prioridad = prioridad
        self.canal_ingreso = canal_ingreso
        self.fecha_creacion = (
            datetime.strptime(fecha_creacion, "%Y-%m-%d %H:%M")
            if fecha_creacion else datetime.now()
        )
        self.observadores = []

    @property
    @abstractmethod
    def tipo(self): pass

    def agregar_observador(self, obs):
        self.observadores.append(obs)

    def notificar(self, mensaje: str):
        for o in self.observadores:
            o.actualizar(mensaje)


class Peticion(PQRS):
    @property
    def tipo(self): return "Peticion"


class Queja(PQRS):
    @property
    def tipo(self): return "Queja"


class Reclamo(PQRS):
    @property
    def tipo(self): return "Reclamo"


class Sugerencia(PQRS):
    @property
    def tipo(self): return "Sugerencia"


# ── FACTORY ─────────────────────────────────────────────────────────────────

class FabricaPQRS:
    MAPA = {"Peticion": Peticion, "Queja": Queja,
            "Reclamo": Reclamo, "Sugerencia": Sugerencia}

    @staticmethod
    def crear(tipo, descripcion, asunto="", cliente_id=0,
              estado="Abierta", radicado=None, prioridad=None,
              canal_ingreso="", fecha_creacion=None):
        tipo = tipo.capitalize()
        if tipo not in TIPOS_PQRS:
            raise ValueError("Tipo invalido")
        return FabricaPQRS.MAPA[tipo](
            radicado=radicado or "",
            descripcion=descripcion,
            asunto=asunto,
            cliente_id=cliente_id,
            estado=estado,
            prioridad=prioridad or 4,
            canal_ingreso=canal_ingreso,
            fecha_creacion=fecha_creacion,
        )


# ── GESTOR ──────────────────────────────────────────────────────────────────

class GestorPQRS:
    def __init__(self):
        self._db = BaseDatosPQRS()
        self._estrategia = PrioridadPorTipo()
        self._observadores = [NotificadorCliente(), NotificadorAgente()]

    def _notificar(self, mensaje: str):
        for o in self._observadores:
            o.actualizar(mensaje)

    # ── Clientes ──────────────────────────────────────────────────────────

    def registrar_cliente(self, cedula: str, nombre: str,
                          telefono: str = "", correo: str = "",
                          direccion: str = "", tipo_cliente: str = "") -> dict:
        """Registra un nuevo cliente. Retorna sus datos."""
        cliente_id = self._db.insertar_cliente(
            cedula, nombre, telefono, correo, direccion, tipo_cliente
        )
        cliente = self._db.buscar_cliente_por_id(cliente_id)
        self._notificar(f"Cliente {nombre} registrado con cédula {cedula}")
        return cliente

    def buscar_cliente(self, cedula: str) -> dict | None:
        """Busca un cliente por cédula."""
        return self._db.buscar_cliente_por_cedula(cedula.strip())

    def listar_clientes(self) -> list[dict]:
        return self._db.listar_clientes()

    def listar_pqrs_cliente(self, cliente_id: int) -> list[dict]:
        """Retorna todas las PQRS de un cliente."""
        return self._db.listar_pqrs_por_cliente(cliente_id)

    def descargar_plantilla_excel(self, ruta: str) -> None:
        """
        Genera una plantilla Excel con los encabezados requeridos
        para la carga masiva de clientes.
        """
        import pandas as pd

        COLUMNAS = [
            "cedula", "nombre", "telefono", "correo",
            "direccion", "tipo_cliente", "estado_cliente",
        ]
        df = pd.DataFrame(columns=COLUMNAS)
        df.to_excel(ruta, index=False)

    def importar_clientes_excel(self, ruta: str) -> dict:
        """
        Importa clientes desde un archivo Excel (.xlsx) con UPSERT.

        Columnas requeridas:
            cedula, nombre, telefono, correo, direccion, tipo_cliente, estado_cliente

        Lógica UPSERT:
            - Si el cliente NO existe por cédula → INSERT
            - Si el cliente YA existe → UPDATE (solo campos con valor en Excel)

        Retorna un dict con:
            insertados, actualizados, errores, detalles_errores
        """
        import pandas as pd

        COLUMNAS_REQUERIDAS = {"cedula", "nombre", "telefono", "correo",
                               "direccion", "tipo_cliente", "estado_cliente"}

        resumen = {
            "insertados": 0,
            "actualizados": 0,
            "errores": 0,
            "detalles_errores": [],
        }

        # Leer Excel
        try:
            df = pd.read_excel(ruta, dtype=str)
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel: {e}")

        # Validar columnas
        columnas_archivo = set(df.columns.str.strip().str.lower())
        faltantes = COLUMNAS_REQUERIDAS - columnas_archivo
        if faltantes:
            raise ValueError(
                f"Columnas requeridas faltantes: {', '.join(sorted(faltantes))}.\n"
                f"Columnas encontradas: {', '.join(sorted(columnas_archivo))}"
            )

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()

        # Procesar cada fila
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque Excel es 1-based + header
            cedula = str(row.get("cedula", "")).strip()
            nombre = str(row.get("nombre", "")).strip()

            # Validar cédula
            if not cedula:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num}: cédula vacía"
                )
                continue

            # Validar nombre
            if not nombre:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): nombre vacío"
                )
                continue

            # Extraer campos
            telefono = str(row.get("telefono", "")).strip()
            correo = str(row.get("correo", "")).strip()
            direccion = str(row.get("direccion", "")).strip()
            tipo_cliente = str(row.get("tipo_cliente", "")).strip()
            estado_cliente = str(row.get("estado_cliente", "")).strip()

            # Verificar si el cliente ya existe por cédula
            existente = self._db.buscar_cliente_por_cedula(cedula)

            try:
                if existente is None:
                    # INSERT: nuevo cliente
                    self._db.insertar_cliente(
                        cedula, nombre, telefono, correo,
                        direccion, tipo_cliente,
                        estado_cliente or "Activo",
                    )
                    resumen["insertados"] += 1
                else:
                    # UPDATE: solo campos con valor en Excel
                    upd_nombre = nombre if nombre else existente["nombre"]
                    upd_telefono = telefono if telefono else existente["telefono"]
                    upd_correo = correo if correo else existente["correo"]
                    upd_direccion = direccion if direccion else existente["direccion"]
                    upd_tipo_cliente = tipo_cliente if tipo_cliente else existente["tipo_cliente"]
                    upd_estado_cliente = estado_cliente if estado_cliente else existente["estado_cliente"]

                    self._db.actualizar_cliente(
                        existente["id"],
                        upd_nombre, upd_telefono, upd_correo,
                        upd_direccion, upd_tipo_cliente, upd_estado_cliente,
                    )
                    resumen["actualizados"] += 1
            except Exception as e:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): error - {e}"
                )

        self._notificar(
            f"Importación Excel completada: {resumen['insertados']} insertados, "
            f"{resumen['actualizados']} actualizados, {resumen['errores']} errores"
        )
        return resumen

    def importar_pqrs_excel(self, ruta: str) -> dict:
        """
        Importa PQRS desde un archivo Excel (.xlsx).

        Columnas requeridas:
            cedula, tipo, canal, asunto, descripcion, estado_inicial, comentario_inicial

        Reglas:
            - Busca cliente por cédula
            - Si existe → crea PQRS
            - Si no existe → error
            - Si comentario_inicial tiene valor → crea log COMENTARIO

        Retorna un dict con:
            insertadas, errores, detalles_errores
        """
        import pandas as pd

        COLUMNAS_REQUERIDAS = {"cedula", "tipo", "canal", "asunto",
                               "descripcion", "estado_inicial", "comentario_inicial"}

        resumen = {
            "insertadas": 0,
            "errores": 0,
            "detalles_errores": [],
        }

        # Leer Excel
        try:
            df = pd.read_excel(ruta, dtype=str)
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel: {e}")

        # Validar columnas
        columnas_archivo = set(df.columns.str.strip().str.lower())
        faltantes = COLUMNAS_REQUERIDAS - columnas_archivo
        if faltantes:
            raise ValueError(
                f"Columnas requeridas faltantes: {', '.join(sorted(faltantes))}.\n"
                f"Columnas encontradas: {', '.join(sorted(columnas_archivo))}"
            )

        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()

        # Procesar cada fila
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque Excel es 1-based + header
            cedula = str(row.get("cedula", "")).strip()

            if not cedula:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num}: cédula vacía"
                )
                continue

            # Buscar cliente por cédula
            cliente = self._db.buscar_cliente_por_cedula(cedula)
            if cliente is None:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): cliente no encontrado"
                )
                continue

            tipo = str(row.get("tipo", "")).strip()
            canal = str(row.get("canal", "")).strip()
            asunto = str(row.get("asunto", "")).strip()
            descripcion = str(row.get("descripcion", "")).strip()
            estado_inicial = str(row.get("estado_inicial", "")).strip()
            comentario_inicial = str(row.get("comentario_inicial", "")).strip()

            if not descripcion:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): descripción vacía"
                )
                continue

            if not tipo:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): tipo vacío"
                )
                continue

            try:
                # Crear PQRS via Factory
                pqrs = FabricaPQRS.crear(
                    tipo, descripcion,
                    asunto=asunto,
                    cliente_id=cliente["id"],
                    estado=estado_inicial if estado_inicial in ESTADOS_VALIDOS else "Abierta",
                    canal_ingreso=canal,
                )

                # Asignar radicado
                pqrs.radicado = _nuevo_radicado(self._db)

                # Calcular prioridad
                pqrs.prioridad = self._estrategia.calcular_prioridad(pqrs.tipo)

                # Persistir
                fecha_str = pqrs.fecha_creacion.strftime("%Y-%m-%d %H:%M")
                estado_final = estado_inicial if estado_inicial in ESTADOS_VALIDOS else "Abierta"
                pqrs_id = self._db.insertar_pqrs(
                    radicado=pqrs.radicado,
                    cliente_id=cliente["id"],
                    tipo=pqrs.tipo,
                    asunto=asunto,
                    descripcion=descripcion,
                    prioridad=pqrs.prioridad,
                    estado=estado_final,
                    canal_ingreso=canal,
                    fecha_creacion=fecha_str,
                )

                # Log de CREACION
                self._db.insertar_log(
                    pqrs_id=pqrs_id,
                    tipo_evento="CREACION",
                    estado_anterior=None,
                    estado_nuevo=estado_final,
                    comentario=f"Creación de {pqrs.tipo} (importación masiva)",
                    usuario="Sistema",
                )

                # Si hay comentario_inicial, crear log COMENTARIO
                if comentario_inicial:
                    self._db.insertar_log(
                        pqrs_id=pqrs_id,
                        tipo_evento="COMENTARIO",
                        estado_anterior=estado_final,
                        estado_nuevo=estado_final,
                        comentario=comentario_inicial,
                        usuario="Sistema",
                    )

                resumen["insertadas"] += 1

            except Exception as e:
                resumen["errores"] += 1
                resumen["detalles_errores"].append(
                    f"Fila {fila_num} (cédula {cedula}): error - {e}"
                )

        self._notificar(
            f"Importación PQRS Excel completada: {resumen['insertadas']} insertadas, "
            f"{resumen['errores']} errores"
        )
        return resumen

    def descargar_plantilla_pqrs_excel(self, ruta: str) -> None:
        """
        Genera una plantilla Excel con los encabezados requeridos
        para la carga masiva de PQRS, incluyendo una fila de ejemplo.
        """
        import pandas as pd

        COLUMNAS = [
            "cedula", "tipo", "canal", "asunto",
            "descripcion", "estado_inicial", "comentario_inicial",
        ]
        df = pd.DataFrame(columns=COLUMNAS)
        # Agregar fila de ejemplo
        ejemplo = {
            "cedula": "1234567890",
            "tipo": "Peticion",
            "canal": "Web",
            "asunto": "Solicitud de información",
            "descripcion": "Ejemplo: describa aquí su solicitud",
            "estado_inicial": "Abierta",
            "comentario_inicial": "Comentario opcional al crear la PQRS",
        }
        df = pd.concat([df, pd.DataFrame([ejemplo])], ignore_index=True)
        df.to_excel(ruta, index=False)

    def listar_pqrs_abiertas(self) -> list[dict]:
        """
        Lista todas las PQRS no cerradas, ordenadas por prioridad ASC, fecha_creacion ASC.
        """
        return self._db.listar_pqrs_abiertas()

    # ── PQRS ──────────────────────────────────────────────────────────────

    def crear_pqrs(self, tipo: str, descripcion: str,
                   cliente_id: int, asunto: str = "",
                   canal_ingreso: str = "") -> dict:
        """
        Crea una PQRS para un cliente existente.
        Lanza ValueError si el cliente no existe.
        """
        # Validar que el cliente exista
        cliente = self._db.buscar_cliente_por_id(cliente_id)
        if cliente is None:
            raise ValueError(f"El cliente con ID {cliente_id} no existe.")

        # Crear objeto PQRS via Factory
        pqrs = FabricaPQRS.crear(
            tipo, descripcion,
            asunto=asunto,
            cliente_id=cliente_id,
            estado="Abierta",
            canal_ingreso=canal_ingreso,
        )

        # Asignar radicado
        pqrs.radicado = _nuevo_radicado(self._db)

        # Calcular prioridad
        pqrs.prioridad = self._estrategia.calcular_prioridad(pqrs.tipo)

        # Persistir
        fecha_str = pqrs.fecha_creacion.strftime("%Y-%m-%d %H:%M")
        pqrs_id = self._db.insertar_pqrs(
            radicado=pqrs.radicado,
            cliente_id=cliente_id,
            tipo=pqrs.tipo,
            asunto=asunto,
            descripcion=descripcion,
            prioridad=pqrs.prioridad,
            estado="Abierta",
            canal_ingreso=canal_ingreso,
            fecha_creacion=fecha_str,
        )

        # Log de CREACION
        self._db.insertar_log(
            pqrs_id=pqrs_id,
            tipo_evento="CREACION",
            estado_anterior=None,
            estado_nuevo="Abierta",
            comentario=f"Creación de {pqrs.tipo}",
            usuario="Sistema",
        )

        self._notificar(f"PQRS {pqrs.radicado} creada para {cliente['nombre']}")

        return {
            "id":         pqrs_id,
            "radicado":   pqrs.radicado,
            "tipo":       pqrs.tipo,
            "asunto":     asunto,
            "prioridad":  pqrs.prioridad,
            "estado":     "Abierta",
            "cliente":    cliente["nombre"],
            "cliente_id": cliente_id,
            "fecha":      fecha_str,
        }

    def listar(self) -> list[dict]:
        """Devuelve todas las PQRS desde la BD."""
        return self._db.listar_pqrs()

    def buscar(self, radicado: str) -> dict | None:
        """Busca por radicado en la BD."""
        return self._db.buscar_pqrs(radicado)

    def siguiente(self) -> dict | None:
        """
        Atiende la PQRS más urgente:
        - Cambia su estado de 'Abierta' → 'En_Proceso'
        - Registra log CAMBIO_ESTADO
        - NO elimina el registro
        """
        dato = self._db.siguiente()
        if dato is None:
            return None
        # Registrar log
        self._db.insertar_log(
            pqrs_id=dato["id"],
            tipo_evento="CAMBIO_ESTADO",
            estado_anterior="Abierta",
            estado_nuevo="En_Proceso",
            comentario="Atendida automáticamente",
            usuario="Sistema",
        )
        self._notificar(f"PQRS {dato['radicado']} atendida → En_Proceso")
        return dato

    def ver_mas_urgente(self) -> dict | None:
        """Retorna la PQRS más urgente sin modificar nada."""
        return self._db.ver_mas_urgente()

    def cambiar_estado(self, radicado: str, nuevo_estado: str,
                       usuario: str = "Sistema",
                       comentario: str = "") -> bool:
        """
        Cambia el estado de una PQRS.
        Registra log CAMBIO_ESTADO.
        Retorna True si tuvo éxito.
        """
        if nuevo_estado not in ESTADOS_VALIDOS:
            return False

        actual = self._db.buscar_pqrs(radicado)
        if actual is None:
            return False
        estado_anterior = actual["estado"]
        pqrs_id = actual["id"]

        ok = self._db.actualizar_estado_pqrs(radicado, nuevo_estado)
        if not ok:
            return False

        # Log CAMBIO_ESTADO
        self._db.insertar_log(
            pqrs_id=pqrs_id,
            tipo_evento="CAMBIO_ESTADO",
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            comentario=comentario,
            usuario=usuario,
        )

        self._notificar(f"Estado cambiado a {nuevo_estado}")
        return ok

    def agregar_comentario(self, radicado: str, comentario: str,
                           usuario: str = "Sistema") -> bool:
        """
        Agrega un comentario a una PQRS (log COMENTARIO).
        No cambia el estado.
        """
        if not comentario.strip():
            return False
        actual = self._db.buscar_pqrs(radicado)
        if actual is None:
            return False

        self._db.insertar_log(
            pqrs_id=actual["id"],
            tipo_evento="COMENTARIO",
            estado_anterior=actual["estado"],
            estado_nuevo=actual["estado"],
            comentario=comentario.strip(),
            usuario=usuario,
        )
        self._notificar(f"Comentario agregado a {radicado}")
        return True

    # ── Historial / Logs ──────────────────────────────────────────────────

    def ver_historial_pqrs(self, radicado: str) -> list[dict]:
        """Retorna los logs de una PQRS."""
        actual = self._db.buscar_pqrs(radicado)
        if actual is None:
            return []
        return self._db.ver_logs_pqrs(actual["id"])

    def ver_historial_cliente(self, cliente_id: int) -> list[dict]:
        """Retorna todos los logs de todas las PQRS de un cliente."""
        return self._db.ver_logs_cliente(cliente_id)
