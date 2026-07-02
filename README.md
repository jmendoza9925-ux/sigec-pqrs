# SIGEC — Sistema Integral de Gestión de Experiencia del Cliente

Sistema de escritorio para la gestión integral de PQRS (Peticiones, Quejas, Reclamos y Sugerencias) de clientes. Construido con Python y Tkinter, sigue una arquitectura MVC con patrones de diseño Factory, Strategy y Observer.

## Problema

En muchas organizaciones, la gestión de clientes y PQRS se realiza de forma manual o en múltiples herramientas aisladas, generando pérdida de trazabilidad, retrasos en la atención, duplicidad de información y dificultad para priorizar casos críticos.

Esta problemática afecta la eficiencia operativa y la calidad del servicio al cliente, especialmente cuando se manejan grandes volúmenes de solicitudes.

SIGEC surge como solución para centralizar, organizar y optimizar este proceso.

## Objetivo

Desarrollar una aplicación de escritorio que permita gestionar clientes y administrar PQRS de forma centralizada, integrando funcionalidades de registro, consulta, actualización, seguimiento y trazabilidad mediante una interfaz gráfica conectada a una base de datos.

El sistema busca mejorar la organización, priorización y control de las solicitudes, facilitando la toma de decisiones y reduciendo tiempos de respuesta.

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

## Base de Datos

SIGEC utiliza SQLite como motor de persistencia local, permitiendo almacenar y consultar información de forma rápida y estructurada.

El sistema se compone de tres tablas principales:

### clientes

Almacena la información maestra de cada cliente.

Campos principales:

- id
- cedula
- nombre
- telefono
- correo
- direccion
- tipo_cliente
- estado_cliente

### pqrs

Contiene las solicitudes registradas por los clientes.

Campos principales:

- id
- radicado
- cliente_id
- tipo
- asunto
- descripcion
- prioridad
- estado
- canal_ingreso
- fecha_creacion

### pqrs_logs

Registra la trazabilidad completa de cada PQRS.

Campos principales:

- id
- pqrs_id
- tipo_evento
- estado_anterior
- estado_nuevo
- comentario
- usuario
- fecha_evento

### Relaciones

Cliente (1) → (N) PQRS  
PQRS (1) → (N) Logs

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

## Beneficios

SIGEC aporta múltiples beneficios operativos:

- Centralización de la información del cliente.
- Registro estructurado de solicitudes PQRS.
- Priorización automática según tipo de requerimiento.
- Seguimiento completo mediante historial y trazabilidad.
- Reducción de tiempos de respuesta.
- Gestión masiva de clientes y PQRS mediante archivos Excel.
- Mayor control sobre el estado de cada solicitud.
- Mejor experiencia para el usuario final.

## Instalación

```bash
git clone https://github.com/jmendoza9925-ux/sigec-pqrs.git
cd sigec-pqrs
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

Uso académico.

Proyecto desarrollado para la asignatura de Programación Avanzada como evidencia práctica de implementación de interfaces gráficas, persistencia de datos y patrones de diseño.
