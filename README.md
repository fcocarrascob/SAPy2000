# SAPy2000 — SAP2000 Automation Suite

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)](https://www.microsoft.com/windows)

Suite de automatización para **CSI SAP2000** con interfaz gráfica PySide6. Diseñada para ingenieros estructurales que trabajan con normativa chilena (NCh2369:2025, AISC 360), permite automatizar tareas repetitivas de modelación, combinaciones de carga, diseño de fundaciones y placas base, conectándose a SAP2000 vía COM (comtypes).

<!-- 
## Capturas de Pantalla
![Vista principal](docs/screenshots/main_app.png)
-->

## Características

- **Modelo Base NCh2369** — Creación automática de modelos con materiales, patrones de carga, espectros de diseño sísmico y combinaciones LRFD/ASD en un solo clic
- **Combinaciones de Carga** — Lectura, edición y escritura masiva de combinaciones directamente desde/hacia SAP2000
- **Placa Base** — Generación geométrica completa: pernos de anclaje (con rings de malla), silla de anclaje opcional y resortes de balasto
- **Fundaciones** — Diseño de pedestales con Section Designer, secciones de losa, y modelación con vínculos rígidos y resortes
- **Utilidades** — Calculadora de propiedades de secciones AISC, generación de mallas rectangulares y con orificios, visualización de tablas internas SAP2000

## Requisitos Previos

- **Windows 10/11** (SAP2000 es Windows-only)
- **Python 3.10+**
- **CSI SAP2000** instalado (v20+ recomendado) — debe estar abierto antes de conectar
- Acceso COM habilitado en SAP2000

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/SAPy2000.git
cd SAPy2000

# Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
# Aplicación completa (5 pestañas)
python main_app.py

# Módulos individuales (standalone — conectan vía GetActiveObject)
python -m Combinations_Carga.app_combos_gui
python -m Modelo_Base.app_modelo_base_gui
python -m Fundaciones.fundaciones_gui
python -m Placa_Base.app_placabase_gui
python -m Utilidades_MOD.app_utils_gui
```

> **Nota:** SAP2000 debe estar abierto con un modelo cargado antes de conectar desde la aplicación.

## Arquitectura

```
main_app.py              ← Punto de entrada (QMainWindow con pestañas)
sap_interface.py         ← Singleton de conexión SAP2000 (signal connectionChanged)
themes.py                ← Paleta de colores y tema visual
gui_components.py        ← Componentes reutilizables (StyledButton, LogWidget, etc.)
sap_utils_common.py      ← Utilidades compartidas para SAP API
app_logger.py            ← Sistema de logging unificado

Combinations_Carga/      ← Gestor de combinaciones de carga
Modelo_Base/             ← Creación de modelo base NCh2369:2025
Fundaciones/             ← Diseño de fundaciones
Placa_Base/              ← Diseño de placa base
Utilidades_MOD/          ← Mallas, secciones y herramientas

API/                     ← Documentación de referencia CSI OAPI
docs/                    ← Guías de desarrollo
```

Cada módulo sigue una estructura estandarizada:

| Archivo | Responsabilidad |
|---------|----------------|
| `backend.py` | Lógica pura SAP2000 (comtypes, sin PySide6) |
| `*_gui.py` | Widget QWidget (recibe `sap_interface`) |
| `config.py` | Constantes y configuración (opcional) |
| `README.md` | Documentación del módulo con diagrama Mermaid |

## Infraestructura Compartida

| Archivo | Propósito |
|---------|-----------|
| `themes.py` | Tema visual modo claro, paleta de colores, stylesheet global |
| `gui_components.py` | StyledButton, LogWidget, ProgressGroup, ConnectionStatusWidget, InputValidator |
| `sap_utils_common.py` | check_ret_code, safe_sap_call, get_materials_by_type, create_point_safe |
| `app_logger.py` | AppLogger singleton con niveles INFO / SUCCESS / WARNING / ERROR |

## Desarrollo

Consultar [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) para estándares completos.

### Regla de Oro — Retornos comtypes

La API de SAP2000 usa `ByRef`. En Python con comtypes, las funciones retornan **tupla** con todos los valores de salida + código de estado al final:

```python
ret = SapModel.LoadCases.GetNameList()  # → (count, names_tuple, RetCode)
if check_ret_code(ret):                 # RetCode siempre es el último
    count, names = ret[0], ret[1]
```

### Patrón de Inyección de Dependencias

- **Backend**: recibe `sap_model` en constructor — permite testing sin GUI
- **GUI Widget**: recibe `sap_interface`, conecta signal `connectionChanged`

## Tecnologías

| Tecnología | Uso |
|-----------|-----|
| **PySide6** | Interfaz gráfica (Qt6) |
| **comtypes** | Automatización COM SAP2000 |
| **pywin32** | Soporte COM Windows (pythoncom) |
| **matplotlib** | Vista previa de espectros de diseño |
| **markdown** | Renderizado de notas técnicas |

## Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.# SAP2000 Automation Suite

Suite de automatización para CSI SAP2000 con interfaz gráfica PySide6.

Automatiza creación de modelos, combinaciones de carga, diseño de placas base,
fundaciones y más, conectándose a SAP2000 vía COM (comtypes).

## Tecnologías

- **Python 3.10+**
- **PySide6** — Interfaz gráfica
- **comtypes** — Automatización COM SAP2000
- **Normativa** — NCh2369:2025, AISC 360

## Arquitectura

```
main_app.py              ← Punto de entrada (QMainWindow con pestañas)
sap_interface.py         ← Singleton de conexión SAP2000
themes.py                ← Paleta de colores y tema visual
gui_components.py        ← Componentes reutilizables (StyledButton, LogWidget, etc.)
sap_utils_common.py      ← Utilidades compartidas para SAP API
app_logger.py            ← Sistema de logging unificado

Combinations_Carga/      ← Gestor de combinaciones de carga
Modelo_Base/             ← Creación de modelo base NCh2369
Fundaciones/             ← Diseño de fundaciones
Placa_Base/              ← Diseño de placa base
Utilidades_MOD/          ← Mallas, tablas y herramientas
Reportes/                ← Reportes (en transición a PANDOC)

API/                     ← Documentación de referencia CSI OAPI
docs/                    ← Guías de desarrollo
```

## Instalación

```bash
pip install PySide6 comtypes
pip install matplotlib  # Opcional, para vista previa de espectros
```

## Ejecución

```bash
# Aplicación completa
python -m main_app

# Módulos individuales (standalone)
python -m Combinations_Carga.app_combos_gui
python -m Modelo_Base.app_modelo_base_gui
python -m Fundaciones.fundaciones_gui
python -m Placa_Base.app_placabase_gui
python -m Utilidades_MOD.app_utils_gui
```

## Módulos

| Módulo | Descripción |
|--------|-------------|
| **Combinaciones de Carga** | Lee/escribe combinaciones LRFD/ASD desde SAP2000 |
| **Modelo Base** | Crea modelo NCh2369:2025 con materiales, espectros y combos |
| **Fundaciones** | Diseño de pedestales con Section Designer + zapatas |
| **Placa Base** | Diseño de placa base con pernos de anclaje |
| **Utilidades** | Generación de mallas, visualización de tablas SAP |
| **Reportes** | En transición a PANDOC (placeholder) |

## Infraestructura Compartida

| Archivo | Propósito |
|---------|-----------|
| `themes.py` | Tema visual modo claro, paleta de colores, stylesheet global |
| `gui_components.py` | StyledButton, LogWidget, ProgressGroup, ConnectionStatusWidget, InputValidator |
| `sap_utils_common.py` | check_ret_code, safe_sap_call, get_materials_by_type, create_point_safe |
| `app_logger.py` | AppLogger singleton con niveles INFO/SUCCESS/WARNING/ERROR |

## Desarrollo

Consultar [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) para estándares completos.

### Regla de Oro — Retornos comtypes

```python
ret = SapModel.LoadCases.GetNameList()  # → (count, names_tuple, RetCode)
if check_ret_code(ret):                 # RetCode siempre es el último
    count, names = ret[0], ret[1]
```

### Patrón de Inyección

- **Backend**: recibe `sap_model` en constructor
- **GUI Widget**: recibe `sap_interface`, conecta `connectionChanged` signal
3.  **Patrón de Desarrollo**:
    - **Backend Unitario**: Permite probar la lógica sin GUI instanciando el backend y pasándole un modelo.
    - **GUI Decoplada**: La interfaz gráfica no contiene lógica de negocio compleja, solo presentación.
