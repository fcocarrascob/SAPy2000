# Step 5: Módulo Reportes — Placeholder para PANDOC

## Goal
Mover la implementación actual del módulo Reportes a `Reportes/deprecated/`, reemplazar con GUI placeholder y backend vacío preparado para futura implementación con PANDOC.

## Prerequisites
- Steps 1–4 completados y commiteados
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 5.1: Crear carpeta deprecated y mover archivos actuales

- [ ] Crear carpeta `Reportes/deprecated/`
- [ ] Mover los siguientes archivos a `Reportes/deprecated/`:
  - `Reportes/word_service.py` → `Reportes/deprecated/word_service.py`
  - `Reportes/snippet_manager.py` → `Reportes/deprecated/snippet_manager.py`
  - `Reportes/snippet_editor.py` → `Reportes/deprecated/snippet_editor.py`
  - `Reportes/template_engine.py` → `Reportes/deprecated/template_engine.py`
  - `Reportes/equation_translator.py` → `Reportes/deprecated/equation_translator.py`

- [ ] Mover carpetas completas a deprecated:
  - `Reportes/library/` → `Reportes/deprecated/library/`
  - `Reportes/templates/` → `Reportes/deprecated/templates/`
  - `Reportes/tests/` → `Reportes/deprecated/tests/`

Ejecutar en terminal:
```powershell
cd c:\Users\francisco.carrasco\Python\APP_sap2000\SAPy2000

# Crear carpeta deprecated
New-Item -ItemType Directory -Path "Reportes\deprecated" -Force

# Mover archivos Python
Move-Item "Reportes\word_service.py" "Reportes\deprecated\" -Force
Move-Item "Reportes\snippet_manager.py" "Reportes\deprecated\" -Force
Move-Item "Reportes\snippet_editor.py" "Reportes\deprecated\" -Force
Move-Item "Reportes\template_engine.py" "Reportes\deprecated\" -Force
Move-Item "Reportes\equation_translator.py" "Reportes\deprecated\" -Force

# Mover carpetas
Move-Item "Reportes\library" "Reportes\deprecated\" -Force
Move-Item "Reportes\templates" "Reportes\deprecated\" -Force
Move-Item "Reportes\tests" "Reportes\deprecated\" -Force
```

##### Step 5.1 Verification Checklist
- [ ] La carpeta `Reportes/deprecated/` contiene todos los archivos movidos
- [ ] En `Reportes/` solo quedan: `__init__.py`, `report_gui.py`, `report_backend.py`, `README.md`, `deprecated/`

---

#### Step 5.2: Reemplazar `Reportes/report_backend.py` — Backend Vacío

- [ ] Reemplazar el contenido completo de `Reportes/report_backend.py` con:

```python
"""
report_backend.py — Backend del módulo de Reportes (placeholder).

El módulo Reportes está en transición a una implementación basada en PANDOC.
La implementación anterior (Word COM) se encuentra en Reportes/deprecated/.

Futuras funcionalidades:
- Extracción de datos SAP2000 → Markdown
- Generación de reportes vía PANDOC → PDF/DOCX
- Plantillas Markdown con ecuaciones LaTeX
- Tablas automáticas desde DatabaseTables
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app_logger import AppLogger


class ReportBackend:
    """Backend placeholder para el módulo de Reportes con PANDOC."""

    def __init__(self, sap_model=None):
        self.SapModel = sap_model
        self.logger = AppLogger()

    def is_available(self) -> bool:
        """Verifica si el módulo de reportes está disponible."""
        return False  # Implementación pendiente con PANDOC
```

##### Step 5.2 Verification Checklist
- [ ] Sin errores: `python -c "from Reportes.report_backend import ReportBackend; print('OK')"`
- [ ] La clase tiene constructor con patrón de inyección estándar

---

#### Step 5.3: Reemplazar `Reportes/report_gui.py` — GUI Placeholder

- [ ] Reemplazar el contenido completo de `Reportes/report_gui.py` con:

```python
"""
report_gui.py — GUI placeholder del módulo de Reportes.

El módulo Reportes está en transición a PANDOC.
Muestra un mensaje informativo al usuario.
"""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QGroupBox, QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gui_components import StyledButton, LogWidget
from themes import COLORS


class ReportWidget(QWidget):
    """Widget placeholder para el módulo de Reportes."""

    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # --- Título ---
        title = QLabel("📝 Módulo de Reportes")
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {COLORS['primary']};"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- Mensaje informativo ---
        grp_info = QGroupBox("Estado del Módulo")
        grp_layout = QVBoxLayout(grp_info)

        msg = QLabel(
            "Este módulo está en proceso de rediseño.\n\n"
            "La nueva implementación utilizará PANDOC para generar reportes "
            "profesionales en formato PDF y DOCX a partir de plantillas Markdown "
            "con ecuaciones LaTeX y datos extraídos directamente de SAP2000.\n\n"
            "Funcionalidades planificadas:\n"
            "  • Extracción automática de datos SAP2000 → Markdown\n"
            "  • Plantillas personalizables con ecuaciones LaTeX nativas\n"
            "  • Generación PANDOC → PDF / DOCX profesional\n"
            "  • Tablas automáticas de materiales, secciones y resultados\n\n"
            "La implementación anterior (basada en Word COM) se conserva\n"
            "como referencia en la carpeta Reportes/deprecated/."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; line-height: 1.5;")
        grp_layout.addWidget(msg)

        layout.addWidget(grp_info)

        # --- Botón deshabilitado ---
        btn = StyledButton("📄 Generar Reporte (Próximamente)", variant="primary")
        btn.setEnabled(False)
        btn.setToolTip("Funcionalidad en desarrollo — próximamente con PANDOC")
        layout.addWidget(btn, alignment=Qt.AlignCenter)

        # --- Spacer ---
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # --- Log preparado ---
        self.log = LogWidget()
        self.log.log("Módulo de Reportes en transición a PANDOC", level="INFO")
        layout.addWidget(self.log)

        self.setLayout(layout)


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    w = ReportWidget()
    w.resize(600, 500)
    w.show()
    sys.exit(app.exec())
```

##### Step 5.3 Verification Checklist
- [ ] Sin errores al ejecutar `python -m Reportes.report_gui`
- [ ] La ventana muestra el mensaje informativo sobre PANDOC
- [ ] El botón "📄 Generar Reporte (Próximamente)" está deshabilitado
- [ ] El `LogWidget` muestra el mensaje inicial
- [ ] El tema visual se aplica correctamente

---

#### Step 5.4: Actualizar `Reportes/__init__.py`

- [ ] Reemplazar el contenido de `Reportes/__init__.py` con:

```python
# Módulo de Reportes — Placeholder para futura implementación con PANDOC
# La implementación anterior se conserva en Reportes/deprecated/

from .report_gui import ReportWidget
from .report_backend import ReportBackend

__all__ = ['ReportWidget', 'ReportBackend']
```

##### Step 5.4 Verification Checklist
- [ ] Sin errores: `python -c "from Reportes import ReportWidget, ReportBackend; print('OK')"`

---

#### Step 5.5: Actualizar `Reportes/README.md`

- [ ] Reemplazar el contenido de `Reportes/README.md` con:

```markdown
# Módulo Reportes — En Transición a PANDOC

## Estado Actual

Este módulo está en proceso de rediseño. La implementación actual muestra un
placeholder mientras se desarrolla la nueva versión basada en PANDOC.

## Implementación Anterior (deprecated)

La implementación previa utilizaba COM automation con Microsoft Word
(`Word.Application`). Los archivos se conservan como referencia en
`Reportes/deprecated/`:

- `word_service.py` — Servicio de bajo nivel para Word COM
- `snippet_manager.py` — Gestor de snippets JSON
- `snippet_editor.py` — Editor visual de snippets
- `template_engine.py` — Motor de plantillas
- `equation_translator.py` — Traductor LaTeX → UnicodeMath
- `library/` — Snippets JSON predefinidos
- `templates/` — Plantillas de estructura de reportes
- `tests/` — Tests del módulo anterior

## Funcionalidades Planificadas (PANDOC)

1. **Extracción de datos** — SAP2000 → Markdown automatizado
2. **Plantillas Markdown** — Con ecuaciones LaTeX nativas
3. **Generación PANDOC** — Markdown → PDF/DOCX profesional
4. **Tablas automáticas** — Materiales, secciones, resultados, combinaciones

## Arquitectura Futura

| Archivo | Clase | Responsabilidad |
|---------|-------|-----------------|
| `report_backend.py` | `ReportBackend` | Extracción datos SAP → Markdown |
| `report_gui.py` | `ReportWidget` | Interfaz de usuario del módulo |

## Ejecutar Standalone

```bash
python -m Reportes.report_gui
```
```

---

#### Step 5 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: replace Reportes module with PANDOC placeholder, move old impl to deprecated
```

Archivos modificados/creados:
- `Reportes/report_gui.py` (reemplazado)
- `Reportes/report_backend.py` (reemplazado)
- `Reportes/__init__.py` (actualizado)
- `Reportes/README.md` (actualizado)
- `Reportes/deprecated/` (nueva carpeta con archivos movidos)
