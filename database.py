"""
database.py — Capa de persistencia con SQLite (Mini CRM).
Tablas:
  - clientes:        datos maestros de clientes.
  - pqrs:            PQRS vinculada a un cliente (FK clientes.id).
  - pqrs_logs:       bitácora de eventos (CREACION, CAMBIO_ESTADO, COMENTARIO).
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pqrs.db")

# ── Esquema ──────────────────────────────────────────────────────────────────

SQL_CREATE_CLIENTES = """
CREATE TABLE IF NOT EXISTS clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula          TEXT    UNIQUE NOT NULL,
    nombre          TEXT    NOT NULL,
    telefono        TEXT,
    correo          TEXT,
    direccion       TEXT,
    tipo_cliente    TEXT,
    estado_cliente  TEXT    NOT NULL DEFAULT 'Activo',
    fecha_registro  TEXT    NOT NULL
);
"""

SQL_CREATE_PQRS = """
CREATE TABLE IF NOT EXISTS pqrs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    radicado            TEXT    UNIQUE NOT NULL,
    cliente_id          INTEGER NOT NULL,
    tipo                TEXT    NOT NULL,
    asunto              TEXT    NOT NULL DEFAULT '',
    descripcion         TEXT    NOT NULL,
    prioridad           INTEGER NOT NULL DEFAULT 4,
    estado_actual       TEXT    NOT NULL DEFAULT 'Abierta',
    canal_ingreso       TEXT,
    fecha_creacion      TEXT    NOT NULL,
    fecha_actualizacion TEXT    NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);
"""

SQL_CREATE_LOGS = """
CREATE TABLE IF NOT EXISTS pqrs_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pqrs_id         INTEGER NOT NULL,
    tipo_evento     TEXT    NOT NULL,
    estado_anterior TEXT,
    estado_nuevo    TEXT,
    comentario      TEXT,
    usuario         TEXT,
    fecha_evento    TEXT    NOT NULL,
    FOREIGN KEY (pqrs_id) REFERENCES pqrs(id)
);
"""

# ── SQL Clientes ─────────────────────────────────────────────────────────────

SQL_INSERT_CLIENTE = """
INSERT INTO clientes (cedula, nombre, telefono, correo, direccion,
                      tipo_cliente, estado_cliente, fecha_registro)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);
"""

SQL_SELECT_CLIENTE_CEDULA = "SELECT * FROM clientes WHERE cedula = ?;"

SQL_SELECT_CLIENTE_ID = "SELECT * FROM clientes WHERE id = ?;"

SQL_SELECT_ALL_CLIENTES = "SELECT * FROM clientes ORDER BY nombre ASC;"

SQL_UPDATE_CLIENTE = """
UPDATE clientes SET nombre=?, telefono=?, correo=?, direccion=?,
                    tipo_cliente=?, estado_cliente=?
WHERE id = ?;
"""

# ── SQL PQRS ─────────────────────────────────────────────────────────────────

SQL_INSERT_PQRS = """
INSERT INTO pqrs (radicado, cliente_id, tipo, asunto, descripcion,
                  prioridad, estado_actual, canal_ingreso,
                  fecha_creacion, fecha_actualizacion)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

SQL_SELECT_ALL_PQRS = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
ORDER BY p.prioridad ASC, p.fecha_creacion ASC;
"""

SQL_SELECT_PQRS_BY_RADICADO = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.radicado = ?;
"""

SQL_SELECT_PQRS_BY_CLIENTE = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.cliente_id = ?
ORDER BY p.fecha_creacion DESC;
"""

SQL_UPDATE_ESTADO_PQRS = """
UPDATE pqrs SET estado_actual = ?, fecha_actualizacion = ? WHERE radicado = ?;
"""

SQL_SELECT_MAS_URGENTE = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.estado_actual IN ('Abierta', 'En_Proceso', 'Escalada')
ORDER BY p.prioridad ASC, p.fecha_creacion ASC LIMIT 1;
"""

SQL_SELECT_SIGUIENTE = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.estado_actual = 'Abierta'
ORDER BY p.prioridad ASC, p.fecha_creacion ASC LIMIT 1;
"""

SQL_SELECT_ABIERTAS = """
SELECT p.*, c.nombre AS cliente_nombre, c.cedula AS cliente_cedula
FROM pqrs p
JOIN clientes c ON c.id = p.cliente_id
WHERE p.estado_actual != 'Cerrada'
ORDER BY p.prioridad ASC, p.fecha_creacion ASC;
"""

SQL_ULTIMO_RADICADO = """
SELECT radicado FROM pqrs ORDER BY id DESC LIMIT 1;
"""

SQL_COUNT_PQRS = "SELECT COUNT(*) FROM pqrs;"

# ── SQL Logs ─────────────────────────────────────────────────────────────────

SQL_INSERT_LOG = """
INSERT INTO pqrs_logs (pqrs_id, tipo_evento, estado_anterior, estado_nuevo,
                       comentario, usuario, fecha_evento)
VALUES (?, ?, ?, ?, ?, ?, ?);
"""

SQL_SELECT_LOGS_BY_PQRS = """
SELECT * FROM pqrs_logs
WHERE pqrs_id = ?
ORDER BY fecha_evento ASC;
"""

SQL_SELECT_LOGS_BY_CLIENTE = """
SELECT l.*, p.radicado
FROM pqrs_logs l
JOIN pqrs p ON p.id = l.pqrs_id
WHERE p.cliente_id = ?
ORDER BY l.fecha_evento DESC;
"""


# ── Conexión singleton ──────────────────────────────────────────────────────

class BaseDatosPQRS:
    """Administra la conexión a SQLite y provee métodos CRUD."""

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._inicializar()

    def _inicializar(self):
        """Crea las tablas si no existen y ejecuta migraciones."""
        self._conn.execute(SQL_CREATE_CLIENTES)
        self._conn.execute(SQL_CREATE_PQRS)
        self._conn.execute(SQL_CREATE_LOGS)
        self._migrar()
        self._conn.commit()

    def _migrar(self):
        """Migraciones para BD existentes (versión anterior)."""
        # Si la tabla pqrs aún tiene columna 'cliente' (texto), migrar
        try:
            self._conn.execute("ALTER TABLE pqrs ADD COLUMN asunto TEXT NOT NULL DEFAULT '';")
        except sqlite3.OperationalError:
            pass
        try:
            self._conn.execute("ALTER TABLE pqrs ADD COLUMN canal_ingreso TEXT;")
        except sqlite3.OperationalError:
            pass
        try:
            self._conn.execute("ALTER TABLE pqrs ADD COLUMN cliente_id INTEGER REFERENCES clientes(id);")
        except sqlite3.OperationalError:
            pass
        # Migrar pqrs_historial → pqrs_logs si existe la vieja
        try:
            self._conn.execute("SELECT COUNT(*) FROM pqrs_historial;")
            # Si existe, migrar datos
            self._conn.execute("""
                INSERT OR IGNORE INTO pqrs_logs (pqrs_id, tipo_evento, estado_anterior,
                                                  estado_nuevo, comentario, usuario, fecha_evento)
                SELECT pqrs_id, 'CAMBIO_ESTADO', estado_anterior, estado_nuevo,
                       comentario, usuario, fecha_evento
                FROM pqrs_historial;
            """)
            self._conn.execute("DROP TABLE IF EXISTS pqrs_historial;")
        except sqlite3.OperationalError:
            pass

    # ── Helpers ────────────────────────────────────────────────────────────

    def _ahora(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _fila_pqrs_a_dict(self, fila: sqlite3.Row | None) -> dict | None:
        if fila is None:
            return None
        return {
            "id":                 fila["id"],
            "radicado":           fila["radicado"],
            "cliente_id":         fila["cliente_id"],
            "cliente":            fila["cliente_nombre"],
            "cliente_cedula":     fila["cliente_cedula"],
            "tipo":               fila["tipo"],
            "asunto":             fila["asunto"],
            "descripcion":        fila["descripcion"],
            "prioridad":          fila["prioridad"],
            "estado":             fila["estado_actual"],
            "canal_ingreso":      fila["canal_ingreso"],
            "fecha_creacion":     fila["fecha_creacion"],
            "fecha":              fila["fecha_creacion"],
            "fecha_actualizacion": fila["fecha_actualizacion"],
        }

    # ── CRUD Clientes ──────────────────────────────────────────────────────

    def insertar_cliente(self, cedula: str, nombre: str,
                         telefono: str = "", correo: str = "",
                         direccion: str = "", tipo_cliente: str = "",
                         estado_cliente: str = "Activo") -> int:
        ahora = self._ahora()
        cursor = self._conn.execute(SQL_INSERT_CLIENTE, (
            cedula, nombre, telefono, correo, direccion,
            tipo_cliente, estado_cliente, ahora
        ))
        self._conn.commit()
        return cursor.lastrowid

    def buscar_cliente_por_cedula(self, cedula: str) -> dict | None:
        cursor = self._conn.execute(SQL_SELECT_CLIENTE_CEDULA, (cedula,))
        fila = cursor.fetchone()
        if fila is None:
            return None
        return {
            "id":             fila["id"],
            "cedula":         fila["cedula"],
            "nombre":         fila["nombre"],
            "telefono":       fila["telefono"],
            "correo":         fila["correo"],
            "direccion":      fila["direccion"],
            "tipo_cliente":   fila["tipo_cliente"],
            "estado_cliente": fila["estado_cliente"],
            "fecha_registro": fila["fecha_registro"],
        }

    def buscar_cliente_por_id(self, cliente_id: int) -> dict | None:
        cursor = self._conn.execute(SQL_SELECT_CLIENTE_ID, (cliente_id,))
        fila = cursor.fetchone()
        if fila is None:
            return None
        return {
            "id":             fila["id"],
            "cedula":         fila["cedula"],
            "nombre":         fila["nombre"],
            "telefono":       fila["telefono"],
            "correo":         fila["correo"],
            "direccion":      fila["direccion"],
            "tipo_cliente":   fila["tipo_cliente"],
            "estado_cliente": fila["estado_cliente"],
            "fecha_registro": fila["fecha_registro"],
        }

    def listar_clientes(self) -> list[dict]:
        cursor = self._conn.execute(SQL_SELECT_ALL_CLIENTES)
        return [
            {
                "id":             r["id"],
                "cedula":         r["cedula"],
                "nombre":         r["nombre"],
                "telefono":       r["telefono"],
                "correo":         r["correo"],
                "direccion":      r["direccion"],
                "tipo_cliente":   r["tipo_cliente"],
                "estado_cliente": r["estado_cliente"],
                "fecha_registro": r["fecha_registro"],
            }
            for r in cursor.fetchall()
        ]

    def actualizar_cliente(self, cliente_id: int, nombre: str,
                           telefono: str, correo: str, direccion: str,
                           tipo_cliente: str, estado_cliente: str) -> bool:
        cursor = self._conn.execute(SQL_UPDATE_CLIENTE, (
            nombre, telefono, correo, direccion,
            tipo_cliente, estado_cliente, cliente_id
        ))
        self._conn.commit()
        return cursor.rowcount > 0

    # ── CRUD PQRS ──────────────────────────────────────────────────────────

    def insertar_pqrs(self, radicado: str, cliente_id: int,
                      tipo: str, asunto: str, descripcion: str,
                      prioridad: int, estado: str,
                      canal_ingreso: str, fecha_creacion: str) -> int:
        ahora = fecha_creacion or self._ahora()
        cursor = self._conn.execute(SQL_INSERT_PQRS, (
            radicado, cliente_id, tipo, asunto, descripcion,
            prioridad, estado, canal_ingreso, ahora, ahora
        ))
        self._conn.commit()
        return cursor.lastrowid

    def listar_pqrs(self) -> list[dict]:
        cursor = self._conn.execute(SQL_SELECT_ALL_PQRS)
        return [self._fila_pqrs_a_dict(f) for f in cursor.fetchall()]

    def buscar_pqrs(self, radicado: str) -> dict | None:
        cursor = self._conn.execute(SQL_SELECT_PQRS_BY_RADICADO, (radicado,))
        return self._fila_pqrs_a_dict(cursor.fetchone())

    def listar_pqrs_por_cliente(self, cliente_id: int) -> list[dict]:
        cursor = self._conn.execute(SQL_SELECT_PQRS_BY_CLIENTE, (cliente_id,))
        return [self._fila_pqrs_a_dict(f) for f in cursor.fetchall()]

    def actualizar_estado_pqrs(self, radicado: str, nuevo_estado: str) -> bool:
        ahora = self._ahora()
        cursor = self._conn.execute(SQL_UPDATE_ESTADO_PQRS, (nuevo_estado, ahora, radicado))
        self._conn.commit()
        return cursor.rowcount > 0

    def contar_pqrs(self) -> int:
        cursor = self._conn.execute(SQL_COUNT_PQRS)
        return cursor.fetchone()[0]

    def ver_mas_urgente(self) -> dict | None:
        cursor = self._conn.execute(SQL_SELECT_MAS_URGENTE)
        return self._fila_pqrs_a_dict(cursor.fetchone())

    def listar_pqrs_abiertas(self) -> list[dict]:
        """Lista todas las PQRS no cerradas, ordenadas por prioridad ASC, fecha ASC."""
        cursor = self._conn.execute(SQL_SELECT_ABIERTAS)
        return [self._fila_pqrs_a_dict(f) for f in cursor.fetchall()]

    def siguiente(self) -> dict | None:
        """Atiende la PQRS más urgente (solo 'Abierta'): cambia a 'En_Proceso'."""
        cursor = self._conn.execute(SQL_SELECT_SIGUIENTE)
        fila = cursor.fetchone()
        if fila is None:
            return None
        dato = self._fila_pqrs_a_dict(fila)
        if dato["estado"] == "Abierta":
            self.actualizar_estado_pqrs(dato["radicado"], "En_Proceso")
            dato["estado"] = "En_Proceso"
        return dato

    def obtener_ultimo_radicado(self) -> str | None:
        cursor = self._conn.execute(SQL_ULTIMO_RADICADO)
        fila = cursor.fetchone()
        return fila["radicado"] if fila else None

    # ── Logs ───────────────────────────────────────────────────────────────

    def insertar_log(self, pqrs_id: int, tipo_evento: str,
                     estado_anterior: str | None = None,
                     estado_nuevo: str | None = None,
                     comentario: str = "",
                     usuario: str = "Sistema") -> None:
        ahora = self._ahora()
        self._conn.execute(SQL_INSERT_LOG, (
            pqrs_id, tipo_evento, estado_anterior, estado_nuevo,
            comentario, usuario, ahora
        ))
        self._conn.commit()

    def ver_logs_pqrs(self, pqrs_id: int) -> list[dict]:
        cursor = self._conn.execute(SQL_SELECT_LOGS_BY_PQRS, (pqrs_id,))
        return [
            {
                "id":              r["id"],
                "pqrs_id":         r["pqrs_id"],
                "tipo_evento":     r["tipo_evento"],
                "estado_anterior": r["estado_anterior"],
                "estado_nuevo":    r["estado_nuevo"],
                "comentario":      r["comentario"],
                "usuario":         r["usuario"],
                "fecha_evento":    r["fecha_evento"],
            }
            for r in cursor.fetchall()
        ]

    def ver_logs_cliente(self, cliente_id: int) -> list[dict]:
        cursor = self._conn.execute(SQL_SELECT_LOGS_BY_CLIENTE, (cliente_id,))
        return [
            {
                "id":              r["id"],
                "pqrs_id":         r["pqrs_id"],
                "radicado":        r["radicado"],
                "tipo_evento":     r["tipo_evento"],
                "estado_anterior": r["estado_anterior"],
                "estado_nuevo":    r["estado_nuevo"],
                "comentario":      r["comentario"],
                "usuario":         r["usuario"],
                "fecha_evento":    r["fecha_evento"],
            }
            for r in cursor.fetchall()
        ]

    def cerrar(self):
        self._conn.close()
