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
