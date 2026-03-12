# SAP2000 Automation Suite

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
