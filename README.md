# SIGEC — Sistema Integral de Gestión de Experiencia del Cliente

Sistema de escritorio para la gestión integral de PQRS (Peticiones, Quejas, Reclamos y Sugerencias) de clientes. Construido con Python y Tkinter, sigue una arquitectura MVC con patrones de diseño Factory, Strategy y Observer.

## Arquitectura

```
app.py          → Punto de entrada
gui.py          → Vista (interfaz gráfica Tkinter)
controller.py   → Controlador (traduce acciones de UI al backend)
GESTOR.py       → Modelo (lógica de negocio, Factory, Strategy, Observer)
database.py     → Persistencia (SQLite)
```

### Patrones de diseño

- **MVC**: Separación clara entre vista, controlador y modelo.
- **Factory** (`FabricaPQRS`): Creación polimórfica de PQRS según tipo.
- **Strategy** (`EstrategiaPrioridad`): Cálculo de prioridad según tipo de PQRS.
- **Observer** (`NotificadorCliente`, `NotificadorAgente`): Notificaciones ante eventos del sistema.

## Tecnologías

- **Python 3.10+**
- **Tkinter** — Interfaz gráfica nativa
- **SQLite** — Base de datos embebida
- **pandas / openpyxl** — Importación/exportación de Excel

## Funcionalidades

- **Gestión de Clientes**: CRUD completo, búsqueda por cédula, importación masiva desde Excel.
- **Gestión de PQRS**: Creación, cambio de estado, comentarios de seguimiento, trazabilidad completa.
- **Bandeja de PQRS Abiertas**: Vista global de PQRS pendientes ordenadas por prioridad.
- **Historial por Cliente**: Visualización de todas las PQRS de un cliente.
- **Trazabilidad**: Bitácora completa de eventos por PQRS.
- **Importación Masiva**: Carga de clientes y PQRS desde archivos Excel con validación y resumen.
- **Scroll Inteligente**: Interfaz con header fijo y cuerpo scrollable.

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/sigec.git
cd sigec

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

## Estructura de archivos

```
sigec/
├── app.py              # Punto de entrada
├── gui.py              # Interfaz gráfica (Tkinter)
├── controller.py       # Controlador MVC
├── GESTOR.py           # Modelo y lógica de negocio
├── database.py         # Capa de persistencia (SQLite)
├── requirements.txt    # Dependencias del proyecto
├── README.md           # Este archivo
└── .gitignore          # Archivos ignorados por Git
```

## Importación desde Excel

### Clientes

Columnas requeridas: `cedula`, `nombre`, `telefono`, `correo`, `direccion`, `tipo_cliente`, `estado_cliente`

Usar el botón **📥 Importar Clientes** en la sección Clientes. Descargue la plantilla con **📄 Plantilla Clientes**.

### PQRS

Columnas requeridas: `cedula`, `tipo`, `canal`, `asunto`, `descripcion`, `estado_inicial`, `comentario_inicial`

Usar el botón **📥 Importar PQRS** en la sección PQRS. Descargue la plantilla con **📄 Plantilla PQRS**.

## Licencia

MIT
