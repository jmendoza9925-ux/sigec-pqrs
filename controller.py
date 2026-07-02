"""
controller.py — Capa de control: conecta la GUI con el backend GestorPQRS.
Traduce acciones de UI a llamadas al backend (Mini CRM).
"""

from GESTOR import GestorPQRS, TIPOS_PQRS, ESTADOS_VALIDOS


class ControladorPQRS:
    def __init__(self):
        self._gestor = GestorPQRS()

    # ── Consultas de constantes ──────────────────────────────────────────────

    @property
    def tipos(self) -> list[str]:
        return sorted(TIPOS_PQRS)

    @property
    def estados(self) -> list[str]:
        return sorted(ESTADOS_VALIDOS)

    # ── Clientes ─────────────────────────────────────────────────────────────

    def buscar_cliente(self, cedula: str) -> dict | None:
        """Busca un cliente por cédula."""
        return self._gestor.buscar_cliente(cedula.strip())

    def registrar_cliente(self, cedula: str, nombre: str,
                          telefono: str = "", correo: str = "",
                          direccion: str = "",
                          tipo_cliente: str = "") -> dict:
        """Registra un nuevo cliente."""
        if not cedula.strip():
            raise ValueError("La cédula es obligatoria.")
        if not nombre.strip():
            raise ValueError("El nombre es obligatorio.")
        return self._gestor.registrar_cliente(
            cedula.strip(), nombre.strip(),
            telefono.strip(), correo.strip(),
            direccion.strip(), tipo_cliente,
        )

    def importar_clientes_excel(self, ruta: str) -> dict:
        """Importa clientes desde un archivo Excel (UPSERT)."""
        return self._gestor.importar_clientes_excel(ruta)

    def descargar_plantilla_excel(self, ruta: str) -> None:
        """Genera una plantilla Excel con los encabezados requeridos."""
        self._gestor.descargar_plantilla_excel(ruta)

    def importar_pqrs_excel(self, ruta: str) -> dict:
        """Importa PQRS desde un archivo Excel."""
        return self._gestor.importar_pqrs_excel(ruta)

    def descargar_plantilla_pqrs_excel(self, ruta: str) -> None:
        """Genera una plantilla Excel para importar PQRS."""
        self._gestor.descargar_plantilla_pqrs_excel(ruta)

    def listar_pqrs_abiertas(self) -> list[dict]:
        """Lista todas las PQRS no cerradas, ordenadas por prioridad ASC, fecha ASC."""
        return self._gestor.listar_pqrs_abiertas()

    def listar_clientes(self) -> list[dict]:
        return self._gestor.listar_clientes()

    def listar_pqrs_cliente(self, cliente_id: int) -> list[dict]:
        """Retorna todas las PQRS de un cliente."""
        return self._gestor.listar_pqrs_cliente(cliente_id)

    # ── PQRS ─────────────────────────────────────────────────────────────────

    def crear_pqrs(self, tipo: str, descripcion: str,
                   cliente_id: int, asunto: str = "",
                   canal_ingreso: str = "") -> dict:
        """
        Crea una PQRS para un cliente existente.
        Lanza ValueError si el cliente no existe o descripción vacía.
        """
        if not descripcion.strip():
            raise ValueError("La descripción no puede estar vacía.")
        return self._gestor.crear_pqrs(
            tipo, descripcion.strip(),
            cliente_id=cliente_id,
            asunto=asunto.strip(),
            canal_ingreso=canal_ingreso.strip(),
        )

    def listar(self) -> list[dict]:
        """Devuelve todas las PQRS registradas como lista de dicts."""
        return self._gestor.listar()

    def buscar(self, radicado: str) -> dict | None:
        """Busca por radicado; devuelve dict o None."""
        return self._gestor.buscar(radicado.strip())

    def atender_siguiente(self) -> dict | None:
        """
        Atiende la siguiente PQRS en cola:
        - Cambia estado Abierta → En_Proceso
        - Registra log CAMBIO_ESTADO
        - NO elimina el registro
        """
        return self._gestor.siguiente()

    def ver_mas_urgente(self) -> dict | None:
        """Devuelve la PQRS más urgente sin retirarla de la cola."""
        return self._gestor.ver_mas_urgente()

    def cambiar_estado(self, radicado: str, nuevo_estado: str,
                       comentario: str = "") -> bool:
        """Cambia el estado de una PQRS. Registra log."""
        return self._gestor.cambiar_estado(
            radicado.strip(), nuevo_estado,
            comentario=comentario,
        )

    def agregar_comentario(self, radicado: str, comentario: str) -> bool:
        """Agrega un comentario a una PQRS (log COMENTARIO)."""
        return self._gestor.agregar_comentario(radicado.strip(), comentario)

    # ── Historial / Logs ──────────────────────────────────────────────────

    def ver_historial(self, radicado: str) -> list[dict]:
        """Devuelve los logs de una PQRS."""
        return self._gestor.ver_historial_pqrs(radicado.strip())

    def ver_historial_cliente(self, cliente_id: int) -> list[dict]:
        """Devuelve todos los logs de todas las PQRS de un cliente."""
        return self._gestor.ver_historial_cliente(cliente_id)
