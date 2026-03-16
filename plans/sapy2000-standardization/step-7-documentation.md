# Step 7: Documentación de Estándares

## Goal
Crear documentación completa de estándares de desarrollo (`CODING_STANDARDS.md`), actualizar el `README.md` principal y actualizar los READMEs de cada módulo para reflejar los cambios de la estandarización.

## Prerequisites
- Steps 1–6 completados y commiteados
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 7.1: Crear `docs/CODING_STANDARDS.md`

- [x] Crear el archivo `docs/CODING_STANDARDS.md` con el contenido siguiente:

```markdown
# Estándares de Desarrollo — SAP2000 Automation Suite

Guía de estándares para mantener consistencia en el desarrollo de módulos.

---

## 1. Arquitectura de Módulos

Cada módulo sigue esta estructura:

```
Nuevo_Modulo/
├── __init__.py           # Exporta BackendClass y WidgetClass
├── backend.py            # Lógica pura (sin PySide6)
├── *_gui.py              # Widget QWidget (recibe sap_interface)
├── config.py             # Constantes y configuración (opcional)
└── README.md             # Descripción, arquitectura, uso
```

### Backend (Lógica Pura)

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code

class MiBackend:
    def __init__(self, sap_model=None):
        self.SapModel = sap_model
        self.logger = AppLogger()

    def mi_operacion(self):
        if not self.SapModel:
            return None
        ret = self.SapModel.AlgunMetodo()
        if check_ret_code(ret):
            self.logger.success("Operación exitosa")
            return ret[:-1]
        else:
            self.logger.error("Operación fallida")
            return None
```

### GUI Widget

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget, ProgressGroup
from themes import COLORS

class MiWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)
        self.init_ui()

    def on_connection_changed(self, connected):
        # Actualizar estado de botones y backend
        pass
```

---

## 2. Sistema de Temas

### NO usar estilos inline

```python
# ✗ INCORRECTO — Estilo inline
btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

# ✓ CORRECTO — Usar StyledButton
btn = StyledButton("📥 Leer SAP2000", variant="primary")
```

### Variantes de botones disponibles

| Variante    | Color       | Uso |
|-------------|-------------|-----|
| `primary`   | Azul        | Acciones principales (leer, crear, generar) |
| `success`   | Verde       | Acciones de envío/confirmación (enviar, ejecutar, modelar) |
| `warning`   | Naranja     | Acciones con precaución (eliminar items, resetear) |
| `secondary` | Gris claro  | Acciones secundarias (agregar fila, navegar) |

### Usar colores del tema

```python
from themes import COLORS

# Para estilos que no cubren los componentes predefinidos:
widget.setStyleSheet(f"background-color: {COLORS['bg_base']};")
```

---

## 3. Regla de Oro — Retornos comtypes

La API SAP2000 usa `ByRef`. En Python con comtypes, las funciones retornan
**TUPLA** con todos los valores de salida + código de estado **al final**.

```python
# ✗ INCORRECTO
ret = SapModel.Func(param)
if ret != 0: ...

# ✗ ANTICUADO (patrón previo a estandarización)
if ret[-1] == 0:
    count = ret[0]

# ✓ CORRECTO (usar utilidad centralizada)
from sap_utils_common import check_ret_code

ret = SapModel.LoadCases.GetNameList()
if check_ret_code(ret):
    count, names = ret[0], ret[1]
```

---

## 4. Logging

### En Backend: usar `AppLogger`

```python
from app_logger import AppLogger

class MiBackend:
    def __init__(self, sap_model=None):
        self.logger = AppLogger()

    def operacion(self):
        self.logger.info("Iniciando operación...")
        self.logger.success("Operación completada")
        self.logger.warning("Dato inesperado")
        self.logger.error("Falló la operación")
```

### En GUI: usar `LogWidget`

```python
from gui_components import LogWidget

self.log = LogWidget()
layout.addWidget(self.log)

# Registrar mensajes:
self.log.log("Operación completada", level="SUCCESS")
self.log.log("Advertencia: dato faltante", level="WARNING")
```

### NO usar `print()` en producción

```python
# ✗ INCORRECTO
print(f"Error: {e}")

# ✓ CORRECTO
self.logger.error(f"Error: {e}")
```

---

## 5. Validación de Inputs

### Usar `InputValidator` antes de operaciones

```python
from gui_components import InputValidator, show_validation_errors

errors = []
ok, msg = InputValidator.validate_positive(self.input_width.text(), "Ancho")
if not ok:
    errors.append(msg)
ok, msg = InputValidator.validate_required(self.input_name.text(), "Nombre")
if not ok:
    errors.append(msg)

if errors:
    show_validation_errors(self, errors)
    return
```

### Confirmaciones para operaciones destructivas

```python
from gui_components import confirm_action

if not confirm_action(self, "Crear Modelo", "Esto borrará el modelo actual.\n¿Continuar?"):
    return
```

---

## 6. Progreso en Operaciones Largas

```python
from gui_components import ProgressGroup

self.progress_group = ProgressGroup("Progreso")
layout.addWidget(self.progress_group)

# Durante la operación:
self.progress_group.set_visible(True)
self.progress_group.set_progress(45, "Creando nudos...")

# Al finalizar:
self.progress_group.reset()
```

---

## 7. Convenciones de Nombres

### Botones — Usar emojis para claridad visual

| Emoji | Acción |
|-------|--------|
| 📥    | Leer / Importar |
| 📤    | Enviar / Exportar |
| ➕    | Agregar |
| ➖    | Eliminar fila |
| ✨    | Crear (secciones, elementos) |
| 🔌    | Conectar |
| 🏗️    | Modelar / Construir |
| 💾    | Guardar |
| 🔄    | Recargar / Refrescar |
| ✏️    | Editar |
| 🗑    | Eliminar |
| 🚀    | Ejecutar |
| 🔧    | Generar malla / herramientas |
| 📍    | Obtener coordenadas |
| 📄    | Generar reporte |

### Variables y atributos

- `self.SapModel` (mayúscula) — Consistente con API CSI
- `self.sap_interface` — Objeto de conexión compartido
- `self.backend` — Instancia del backend del módulo
- `self.log` — Instancia de LogWidget
- `self.logger` — Instancia de AppLogger (backend)

### Archivos

- `*_backend.py` — Lógica pura del módulo
- `*_gui.py` o `app_*_gui.py` — Widget principal del módulo
- `config.py` — Constantes y configuración

---

## 8. Crear Nuevo Módulo (Checklist)

1. [ ] Crear carpeta `Nuevo_Modulo/` con `__init__.py`
2. [ ] Crear `backend.py` con patrón de inyección (`sap_model=None`)
3. [ ] Agregar `self.logger = AppLogger()` al constructor del backend
4. [ ] Usar `check_ret_code()` para todas las llamadas API
5. [ ] Crear `*_gui.py` con `StyledButton`, `LogWidget`
6. [ ] Recibir `sap_interface` en constructor GUI
7. [ ] Conectar `connectionChanged` signal
8. [ ] Agregar validación de inputs con `InputValidator`
9. [ ] Agregar `confirm_action()` para operaciones destructivas
10. [ ] Crear `README.md` con descripción, arquitectura y diagrama Mermaid
11. [ ] Agregar bloque `if __name__` con `apply_theme(app)`
12. [ ] Registrar en `main_app.py` → `init_tabs()`

---

## 9. Ejecución Standalone

Cada módulo debe soportar ejecución aislada:

```python
if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = MiWidget()
    window.show()
    sys.exit(app.exec())
```
```

##### Step 7.1 Verification Checklist
- [x] El archivo `docs/CODING_STANDARDS.md` existe y es legible
- [x] Los ejemplos de código son correctos y consistentes con la implementación actual

---

#### Step 7.2: Actualizar `README.md` principal

- [x] Reemplazar el contenido de `README.md` en la raíz del proyecto con:

```markdown
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
```

##### Step 7.2 Verification Checklist
- [x] El `README.md` principal refleja la estructura actual del proyecto
- [x] Las secciones listadas de infraestructura coinciden con los archivos creados

---

#### Step 7.3: Actualizar READMEs de Módulos

- [x] Actualizar `Combinations_Carga/README.md` agregando sección de infraestructura:

Agregar al final del archivo:
```markdown

## Infraestructura Utilizada

- **StyledButton** — Botones con variantes (primary para leer, success para enviar)
- **LogWidget** — Log de operaciones con timestamp
- **check_ret_code** — Validación de retornos API SAP2000
- **AppLogger** — Logging en backend

## Ejecutar Standalone

```bash
python -m Combinations_Carga.app_combos_gui
```
```

- [x] Actualizar `Modelo_Base/README.md` agregando sección de infraestructura:

Agregar al final:
```markdown

## Infraestructura Utilizada

- **StyledButton** — Botón "🏗️ Crear Modelo Base" (primary)
- **ProgressGroup** — Barra de progreso durante creación
- **LogWidget** — Log paso a paso de la creación
- **check_ret_code** — Validación de retornos API
- **AppLogger** — Logging en backend
- **confirm_action** — Confirmación con detalle de parámetros

## Ejecutar Standalone

```bash
python -m Modelo_Base.app_modelo_base_gui
```
```

- [x] Actualizar `Fundaciones/README.md` agregando sección equivalente
- [x] Actualizar `Placa_Base/README.md` agregando sección equivalente
- [x] Actualizar `Utilidades_MOD/README.md` agregando sección equivalente

##### Step 7.3 Verification Checklist
- [x] Cada README de módulo menciona los componentes de infraestructura utilizados
- [x] Los comandos de ejecución standalone son correctos

---

#### Step 7.4: Actualizar `.github/copilot-instructions.md`

- [x] Agregar sección sobre la infraestructura nueva al final antes de la sección "Convenciones":

```markdown

## Infraestructura Compartida (Step 1)

La aplicación cuenta con infraestructura centralizada en la raíz:

- **`themes.py`**: Tema visual modo claro. `apply_theme(app)` configura QPalette + stylesheet global. Diccionario `COLORS` con paleta completa. `BUTTON_STYLES` con variantes.
- **`gui_components.py`**: Componentes reutilizables:
  - `StyledButton(text, variant)` — variants: 'primary', 'success', 'warning', 'secondary'
  - `LogWidget()` — QTextEdit de log con `.log(msg, level)` y auto-scroll
  - `ProgressGroup(title)` — QGroupBox con QProgressBar + label de estado
  - `ConnectionStatusWidget()` — Indicador visual de conexión
  - `InputValidator` — Validadores: `validate_numeric()`, `validate_required()`, `validate_positive()`, `validate_coordinates()`
  - `confirm_action(parent, title, msg)` — Diálogo de confirmación
  - `show_validation_errors(parent, errors)` — Muestra errores de validación
- **`sap_utils_common.py`**: `check_ret_code(ret)`, `safe_sap_call()`, `get_materials_by_type()`, `create_point_safe()`
- **`app_logger.py`**: `AppLogger` singleton con `.info()`, `.success()`, `.warning()`, `.error()`

### NO usar estilos inline — usar StyledButton y COLORS del tema

```python
# ✗ Incorrecto
btn.setStyleSheet("background-color: #2196F3; color: white;")

# ✓ Correcto
btn = StyledButton("📥 Leer", variant="primary")
```
```

##### Step 7.4 Verification Checklist
- [x] Las copilot-instructions reflejan la nueva infraestructura
- [x] Copilot podrá usar estos componentes al generar código nuevo

---

#### Step 7 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
docs: add CODING_STANDARDS, update README and module docs for standardization
```

Archivos creados/modificados:
- `docs/CODING_STANDARDS.md` (nuevo)
- `README.md` (actualizado)
- `Combinations_Carga/README.md` (actualizado)
- `Modelo_Base/README.md` (actualizado)
- `Fundaciones/README.md` (actualizado)
- `Placa_Base/README.md` (actualizado)
- `Utilidades_MOD/README.md` (actualizado)
- `.github/copilot-instructions.md` (actualizado)
