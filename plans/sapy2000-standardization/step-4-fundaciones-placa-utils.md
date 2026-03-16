# Step 4: Migración Módulos Fase 2 — Fundaciones, Placa Base y Utilidades

## Goal
Aplicar las transformaciones de estandarización a los 3 módulos restantes: `Fundaciones`, `Placa_Base` y `Utilidades_MOD`, usando los componentes centralizados de infraestructura.

## Prerequisites
- Steps 1, 2 y 3 completados y commiteados
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 4.1: Migrar `Fundaciones/fundaciones_backend.py` — Integrar check_ret_code y Logger

- [x] Aplicar las siguientes modificaciones en `Fundaciones/fundaciones_backend.py`:

**Cambio 1 — Agregar imports de infraestructura** (al inicio del archivo):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code, get_materials_by_type
```

**Cambio 2 — Agregar logger al constructor**:

En el `__init__`, agregar:
```python
        self.logger = AppLogger()
```

**Cambio 3 — Reemplazar `get_concrete_materials()` para usar utilidad compartida**:

Buscar el método `get_concrete_materials` completo y reemplazar con:
```python
    def get_concrete_materials(self):
        """Retorna lista de materiales de hormigón."""
        if not self.SapModel:
            return []
        return get_materials_by_type(self.SapModel, self.eMatType_Concrete)
```

**Cambio 4 — Reemplazar `get_rebar_materials()` para usar utilidad compartida**:

Buscar el método `get_rebar_materials` completo y reemplazar con:
```python
    def get_rebar_materials(self):
        """Retorna lista de materiales de refuerzo."""
        if not self.SapModel:
            return []
        return get_materials_by_type(self.SapModel, self.eMatType_Rebar)
```

**Cambio 5 — Reemplazar `print()` con `self.logger`** en todo el archivo:

- Buscar todas las ocurrencias de `print(f"Error` y reemplazar con `self.logger.error(`
- Buscar todas las ocurrencias de `print(f"Aviso` o `print(f"Advertencia` y reemplazar con `self.logger.warning(`
- Buscar todas las ocurrencias de `print(f"No hay conexión` y reemplazar con `self.logger.warning("No hay conexión con SAP2000")`
- Buscar las ocurrencias de `print(f"✅` y reemplazar con `self.logger.success(`

**Cambio 6 — Reemplazar verificaciones `ret[-1] != 0` con `check_ret_code`**:

En cada método que tenga el patrón:
```python
if ret[-1] != 0:
```
Reemplazar con:
```python
if not check_ret_code(ret):
```

Y donde el patrón sea:
```python
if ret[-1] == 0:
```
Reemplazar con:
```python
if check_ret_code(ret):
```

##### Step 4.1 Verification Checklist
- [ ] Sin errores: `python -c "from Fundaciones.fundaciones_backend import FundacionesBackend; print('OK')"`
- [ ] Ya no hay `print()` directo en el backend, todo usa `self.logger`
- [ ] `get_concrete_materials` y `get_rebar_materials` usan `get_materials_by_type`

---

#### Step 4.2: Migrar `Fundaciones/fundaciones_gui.py` — Integrar Componentes Estandarizados

- [x] Aplicar las siguientes modificaciones en `Fundaciones/fundaciones_gui.py`:

**Cambio 1 — Agregar imports de infraestructura** (después de los imports de PySide6):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget
from themes import COLORS
```

**Cambio 2 — Reemplazar estilos inline del tab_widget**:

Buscar:
```python
self.tab_widget.setStyleSheet("""
    QTabWidget::pane { border: 1px solid #bdc3c7; }
    QTabBar::tab { padding: 8px 20px; font-weight: bold; }
    QTabBar::tab:selected { background: #3498db; color: white; }
""")
```

Reemplazar con (eliminar la línea — el tema global ya estiliza los tabs):
```python
# Estilos de tabs manejados por tema global (themes.py)
```

**Cambio 3 — Reemplazar el botón grande de modelar fundación**:

Buscar:
```python
self.btn_modelar_fundacion = QPushButton("🏗️ MODELAR FUNDACIÓN COMPLETA")
self.btn_modelar_fundacion.setStyleSheet("""
    QPushButton {
        font-size: 12pt;
        font-weight: bold;
        padding: 12px;
        background-color: #27ae60;
        color: white;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #229954;
    }
    QPushButton:disabled {
        background-color: #95a5a6;
    }
""")
```

Reemplazar con:
```python
self.btn_modelar_fundacion = StyledButton("🏗️ MODELAR FUNDACIÓN COMPLETA", variant="success")
```

**Cambio 4 — Reemplazar botones de crear sección con StyledButton**:

Buscar cada instancia de `QPushButton("✨` y reemplazar:

```python
# Antes:
self.btn_create_section = QPushButton("✨ Crear Sección Pedestal")
# Después:
self.btn_create_section = StyledButton("✨ Crear Sección Pedestal", variant="primary")
```

```python
# Antes:
self.btn_create_zapata = QPushButton("✨ Crear Secciones Shell")
# Después:
self.btn_create_zapata = StyledButton("✨ Crear Secciones Shell", variant="primary")
```

**Cambio 5 — Reemplazar el label informativo con estilo inline**:

Buscar:
```python
info_label = QLabel("💡 Se crearán 2 secciones con colores diferentes")
info_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 9pt;")
```

Reemplazar con:
```python
info_label = QLabel("💡 Se crearán 2 secciones con colores diferentes")
info_label.setProperty("role", "info")
```

**Cambio 6 — Reemplazar QTextEdit de log con LogWidget** (si usa QTextEdit para log):

Buscar la instancia de QTextEdit que sirve como log (usualmente en la pestaña "🏗️ Modelar") y reemplazar:

```python
# Antes:
self.log_text = QTextEdit()
self.log_text.setReadOnly(True)
# Después:
self.log_text = LogWidget()
```

Y todos los calls a `self.log_text.append(...)` deben cambiarse a:
```python
self.log_text.log(message, level="INFO")   # para mensajes normales
self.log_text.log(message, level="SUCCESS") # para éxitos
self.log_text.log(message, level="ERROR")   # para errores
```

**Cambio 7 — Actualizar bloque `if __name__`**:

Buscar el bloque `if __name__ == "__main__":` y agregar apply_theme:

```python
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = FundacionesWidget()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
```

##### Step 4.2 Verification Checklist
- [ ] Sin errores al ejecutar `python -m Fundaciones.fundaciones_gui`
- [ ] El botón "🏗️ MODELAR FUNDACIÓN COMPLETA" tiene estilo success (verde)
- [ ] Los botones "✨ Crear Sección Pedestal" y "✨ Crear Secciones Shell" tienen estilo primary (azul)
- [ ] El log usa `LogWidget` con formato de timestamp
- [ ] Los tabs tienen el estilo del tema global

---

#### Step 4.3: Migrar `Placa_Base/placabase_backend.py` — Integrar check_ret_code y Logger

- [x] Aplicar las siguientes modificaciones en `Placa_Base/placabase_backend.py`:

**Cambio 1 — Agregar imports de infraestructura** (al inicio del archivo):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code
```

**Cambio 2 — Actualizar el constructor**:

Buscar:
```python
def __init__(self, sap_model=None, logger=None):
    self.SapModel = sap_model
    self.logger = logger
    self.config = PlateConfig()
```

Reemplazar con:
```python
def __init__(self, sap_model=None, logger=None):
    self.SapModel = sap_model
    self.logger = logger or AppLogger()
    self.config = PlateConfig()
```

**Cambio 3 — Actualizar `_check_ret` para usar `check_ret_code`**:

Buscar el método `_check_ret` completo y reemplazar con:
```python
def _check_ret(self, ret, success_msg="", error_msg="") -> bool:
    if check_ret_code(ret):
        if success_msg:
            self.log(success_msg)
        return True
    else:
        code = ret[-1] if isinstance(ret, (tuple, list)) and len(ret) > 0 else ret
        if error_msg:
            self.log(f"{error_msg} (Code: {code})")
        return False
```

##### Step 4.3 Verification Checklist
- [ ] Sin errores: `python -c "from Placa_Base.placabase_backend import BasePlateBackend; print('OK')"`
- [ ] `_check_ret` ahora delega a `check_ret_code` centralizado

---

#### Step 4.4: Migrar `Placa_Base/app_placabase_gui.py` — Integrar Componentes Estandarizados

- [x] Aplicar las siguientes modificaciones en `Placa_Base/app_placabase_gui.py`:

**Cambio 1 — Agregar imports de infraestructura** (después de los imports de PySide6):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget
from themes import COLORS
```

**Cambio 2 — Reemplazar botón "Guardar y Ejecutar" con StyledButton**:

Buscar:
```python
self.run_btn = QPushButton('Guardar y Ejecutar')
```

Reemplazar con:
```python
self.run_btn = StyledButton('🚀 Guardar y Ejecutar', variant="success")
```

**Cambio 3 — Reemplazar botones con StyledButton**:

```python
# Antes:
self.add_row_btn = QPushButton('Agregar fila')
self.remove_row_btn = QPushButton('Eliminar fila')
self.generate_preset_btn = QPushButton('Generar posiciones (preset)')

# Después:
self.add_row_btn = StyledButton('➕ Agregar fila', variant="secondary")
self.remove_row_btn = StyledButton('➖ Eliminar fila', variant="secondary")
self.generate_preset_btn = StyledButton('Generar posiciones (preset)', variant="secondary")
```

**Cambio 4 — Reemplazar QTextEdit de log con LogWidget** (si usa QTextEdit para log de ejecución):

Buscar la instancia de QTextEdit que sirve como log y reemplazar con:
```python
self.log_text = LogWidget()
```

Y actualizar los `self.log_text.append(...)` a `self.log_text.log(message, level="INFO")`.

**Cambio 5 — Actualizar `on_connection_changed`**:

Buscar:
```python
def on_connection_changed(self, connected):
    self.run_btn.setEnabled(connected)
    if connected:
        self.run_btn.setToolTip("Guardar configuración y ejecutar en SAP2000")
        self.run_btn.setText("Guardar y Ejecutar")
        self.load_materials_from_model()
    else:
        self.run_btn.setToolTip("Conecte SAP2000 para ejecutar")
        self.run_btn.setText("Guardar y Ejecutar (Sin Conexión)")
```

Reemplazar con:
```python
def on_connection_changed(self, connected):
    self.run_btn.setEnabled(connected)
    if connected:
        self.run_btn.setToolTip("Guardar configuración y ejecutar en SAP2000")
        self.run_btn.setText("🚀 Guardar y Ejecutar")
        self.load_materials_from_model()
    else:
        self.run_btn.setToolTip("Conecte SAP2000 para ejecutar")
        self.run_btn.setText("🚀 Guardar y Ejecutar (Sin Conexión)")
```

**Cambio 6 — Actualizar bloque `if __name__`**:

```python
if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    w = MainWindow()
    w.resize(700, 600)
    w.show()
    sys.exit(app.exec())
```

##### Step 4.4 Verification Checklist
- [ ] Sin errores al ejecutar `python -m Placa_Base.app_placabase_gui`
- [ ] El botón "🚀 Guardar y Ejecutar" tiene estilo success (verde)
- [ ] Los botones de agregar/eliminar fila usan StyledButton secondary
- [ ] El log usa `LogWidget` con formato de timestamp

---

#### Step 4.5: Migrar `Utilidades_MOD/utils_backend.py` — Integrar check_ret_code y Logger

- [x] Aplicar las siguientes modificaciones en `Utilidades_MOD/utils_backend.py`:

**Cambio 1 — Agregar imports de infraestructura** (al inicio):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app_logger import AppLogger
from sap_utils_common import check_ret_code
```

**Cambio 2 — Agregar logger al constructor**:

En el `__init__`, agregar:
```python
        self.logger = AppLogger()
```

**Cambio 3 — Reemplazar `print()` con `self.logger`** en todo el archivo:

- Todas las `print(f"Error` → `self.logger.error(`
- Todas las `print(f"No hay conexión` → `self.logger.warning("No hay conexión con SAP2000")`

**Cambio 4 — Reemplazar verificaciones directas de ret code**:

Donde exista el patrón:
```python
if isinstance(ret, (list, tuple)):
    ret_code = ret[-1]
elif isinstance(ret, int):
    ret_code = ret
if ret_code == 0:
```

Simplificar a:
```python
if check_ret_code(ret):
```

##### Step 4.5 Verification Checklist
- [ ] Sin errores: `python -c "from Utilidades_MOD.utils_backend import SapUtils; print('OK')"`
- [ ] Ya no hay `print()` directo en el backend

---

#### Step 4.6: Migrar `Utilidades_MOD/app_utils_gui.py` — Integrar Componentes Estandarizados

- [x] Aplicar las siguientes modificaciones en `Utilidades_MOD/app_utils_gui.py`:

**Cambio 1 — Agregar imports de infraestructura** (después de los imports de PySide6):

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget
from themes import COLORS
```

**Cambio 2 — Reemplazar botones clave con StyledButton**:

```python
# Antes:
self.generate_btn = QPushButton("Generar Malla")
# Después:
self.generate_btn = StyledButton("🔧 Generar Malla", variant="primary")
```

```python
# Antes:
self.btn_get_coords = QPushButton("Obtener Coordenadas")
# Después:
self.btn_get_coords = StyledButton("📍 Obtener Coordenadas", variant="secondary")
```

```python
# Antes:
self.btn_load = QPushButton("Cargar Tabla")
# Después:
self.btn_load = StyledButton("📥 Cargar Tabla", variant="primary")
```

```python
# Antes:
self.btn_refresh = QPushButton("↻ Actualizar Lista")
# Después:
self.btn_refresh = StyledButton("🔄 Actualizar Lista", variant="secondary")
```

**Cambio 3 — Eliminar estilos inline de PreviewWidget**:

Buscar:
```python
self.setStyleSheet("background-color: white; border: 1px solid #999;")
```

Reemplazar con:
```python
self.setStyleSheet(f"background-color: {COLORS['bg_base']}; border: 1px solid {COLORS['border']};")
```

**Cambio 4 — Eliminar estilos inline de botones pequeños**:

Buscar:
```python
btn.setStyleSheet("font-size: 10px; padding: 2px;")
```

Dejar sin setStyleSheet (el tema global maneja los estilos) o reemplazar con:
```python
btn.setMaximumHeight(20)
```

**Cambio 5 — Actualizar bloque `if __name__`**:

```python
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

##### Step 4.6 Verification Checklist
- [ ] Sin errores al ejecutar `python -m Utilidades_MOD.app_utils_gui`
- [ ] El botón "🔧 Generar Malla" tiene estilo primary (azul)
- [ ] El PreviewWidget usa colores del tema
- [ ] Los tabs heredan el estilo del tema global

---

#### Step 4 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: migrate Fundaciones, Placa_Base and Utilidades_MOD to centralized infrastructure
```

Archivos modificados:
- `Fundaciones/fundaciones_backend.py`
- `Fundaciones/fundaciones_gui.py`
- `Placa_Base/placabase_backend.py`
- `Placa_Base/app_placabase_gui.py`
- `Utilidades_MOD/utils_backend.py`
- `Utilidades_MOD/app_utils_gui.py`
