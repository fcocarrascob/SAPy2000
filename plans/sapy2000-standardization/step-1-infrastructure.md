# Step 1: Infraestructura Base - Sistema de Temas y Utilidades Compartidas

## Goal
Crear los 4 archivos de infraestructura centralizada (`themes.py`, `gui_components.py`, `sap_utils_common.py`, `app_logger.py`) que servirán como base para toda la estandarización.

## Prerequisites
Make sure that the user is currently on the `feature/standardization-gui-ux` branch before beginning implementation.
If not, move them to the correct branch. If the branch does not exist, create it from main.

---

### Step-by-Step Instructions

#### Step 1.1: Crear `app_logger.py` — Sistema de Logging Unificado

- [ ] Crear el archivo `app_logger.py` en la raíz del proyecto
- [ ] Copiar y pegar el código siguiente en `app_logger.py`:

```python
"""
app_logger.py — Sistema de logging unificado para SAP2000 Automation Suite.

Singleton AppLogger con niveles INFO, WARNING, ERROR, SUCCESS.
Formato consistente con timestamp y prefijo visual.
Opción de exportar log a archivo.
"""

import os
from datetime import datetime
from typing import Optional, List, Callable


class AppLogger:
    """
    Logger singleton para toda la aplicación.
    Almacena mensajes en memoria y opcionalmente escribe a archivo.
    Soporta callbacks para conectar con LogWidget de GUI.
    """

    _instance: Optional["AppLogger"] = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._entries: List[str] = []
        self._callbacks: List[Callable[[str, str], None]] = []
        self._log_file: Optional[str] = None

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------

    def set_log_file(self, path: str):
        """Define ruta de archivo para persistencia de logs."""
        self._log_file = path

    def add_callback(self, cb: Callable[[str, str], None]):
        """
        Registra un callback que se invoca en cada mensaje.
        Firma: cb(level: str, formatted_message: str)
        """
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    def remove_callback(self, cb: Callable[[str, str], None]):
        """Elimina un callback previamente registrado."""
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    # ------------------------------------------------------------------
    # Emisión de mensajes
    # ------------------------------------------------------------------

    def _emit(self, level: str, prefix: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {prefix} {message}"
        self._entries.append(formatted)

        # Consola
        print(formatted)

        # Archivo (si configurado)
        if self._log_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except OSError:
                pass

        # Callbacks (GUI LogWidget, etc.)
        for cb in self._callbacks:
            try:
                cb(level, formatted)
            except Exception:
                pass

    def info(self, message: str):
        self._emit("INFO", "ℹ️", message)

    def success(self, message: str):
        self._emit("SUCCESS", "✅", message)

    def warning(self, message: str):
        self._emit("WARNING", "⚠️", message)

    def error(self, message: str):
        self._emit("ERROR", "❌", message)

    # ------------------------------------------------------------------
    # Consulta y exportación
    # ------------------------------------------------------------------

    def get_entries(self) -> List[str]:
        """Retorna copia de todas las entradas del log."""
        return list(self._entries)

    def clear(self):
        """Limpia las entradas en memoria (no afecta el archivo)."""
        self._entries.clear()

    def export_to_file(self, path: str) -> bool:
        """Exporta el log completo a un archivo de texto."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._entries))
            return True
        except OSError:
            return False

    @classmethod
    def reset(cls):
        """Resetea el singleton (útil para testing)."""
        cls._instance = None
```

##### Step 1.1 Verification Checklist
- [ ] El archivo `app_logger.py` existe en la raíz del proyecto
- [ ] Test rápido en terminal:
  ```bash
  python -c "from app_logger import AppLogger; log = AppLogger(); log.info('Test'); log.success('OK'); log.warning('Ojo'); log.error('Fallo'); print(len(log.get_entries()))"
  ```
  Debe imprimir 4 mensajes formateados con timestamp y luego `4`

---

#### Step 1.2: Crear `themes.py` — Paleta de Colores y Tema Visual

- [ ] Crear el archivo `themes.py` en la raíz del proyecto
- [ ] Copiar y pegar el código siguiente en `themes.py`:

```python
"""
themes.py — Sistema de temas centralizado para SAP2000 Automation Suite.

Define paleta de colores modo claro, esquemas para botones/tabs/inputs,
y función apply_theme(app) que configura QPalette + stylesheet global.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


# ======================================================================
# Paleta de colores — Modo Claro Profesional
# ======================================================================

COLORS = {
    # Fondos
    "bg_window":        "#F5F5F5",
    "bg_base":          "#FFFFFF",
    "bg_alt":           "#FAFAFA",
    "bg_card":          "#FFFFFF",

    # Texto
    "text_primary":     "#212121",
    "text_secondary":   "#616161",
    "text_disabled":    "#9E9E9E",
    "text_placeholder": "#BDBDBD",

    # Acentos
    "primary":          "#1565C0",      # Azul profesional
    "primary_light":    "#1E88E5",
    "primary_dark":     "#0D47A1",
    "primary_surface":  "#E3F2FD",

    "success":          "#2E7D32",
    "success_light":    "#4CAF50",
    "success_surface":  "#E8F5E9",

    "warning":          "#E65100",
    "warning_light":    "#FF9800",
    "warning_surface":  "#FFF3E0",

    "error":            "#C62828",
    "error_light":      "#EF5350",
    "error_surface":    "#FFEBEE",

    # Bordes y separadores
    "border":           "#E0E0E0",
    "border_focus":     "#1565C0",
    "divider":          "#EEEEEE",

    # Componentes
    "tab_active_bg":    "#FFFFFF",
    "tab_inactive_bg":  "#EEEEEE",
    "toolbar_bg":       "#FAFAFA",
    "statusbar_bg":     "#F5F5F5",
    "groupbox_border":  "#CFD8DC",

    # Botones variantes
    "btn_secondary_bg":     "#E0E0E0",
    "btn_secondary_hover":  "#BDBDBD",
    "btn_secondary_text":   "#424242",
}


# ======================================================================
# Stylesheet global
# ======================================================================

def _build_stylesheet() -> str:
    c = COLORS
    return f"""
    /* ---- Ventana principal ---- */
    QMainWindow, QDialog {{
        background-color: {c['bg_window']};
    }}

    /* ---- Widgets base ---- */
    QWidget {{
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 13px;
        color: {c['text_primary']};
    }}

    /* ---- Toolbar ---- */
    QToolBar {{
        background-color: {c['toolbar_bg']};
        border-bottom: 1px solid {c['border']};
        padding: 4px 8px;
        spacing: 6px;
    }}

    /* ---- Status bar ---- */
    QStatusBar {{
        background-color: {c['statusbar_bg']};
        border-top: 1px solid {c['border']};
        color: {c['text_secondary']};
        font-size: 12px;
    }}

    /* ---- Tab Widget ---- */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background-color: {c['bg_base']};
    }}
    QTabBar::tab {{
        background-color: {c['tab_inactive_bg']};
        color: {c['text_secondary']};
        padding: 8px 18px;
        border: 1px solid {c['border']};
        border-bottom: none;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['tab_active_bg']};
        color: {c['primary']};
        font-weight: bold;
        border-bottom: 2px solid {c['primary']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['primary_surface']};
    }}

    /* ---- Group Box ---- */
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {c['groupbox_border']};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 18px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        top: 2px;
        padding: 0 6px;
        color: {c['primary']};
    }}

    /* ---- Inputs ---- */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 8px;
        background-color: {c['bg_base']};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c['border_focus']};
    }}
    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {c['bg_alt']};
        color: {c['text_disabled']};
    }}

    /* ---- ComboBox ---- */
    QComboBox {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 8px;
        background-color: {c['bg_base']};
    }}
    QComboBox:focus {{
        border: 2px solid {c['border_focus']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    /* ---- Table ---- */
    QTableWidget {{
        background-color: {c['bg_base']};
        gridline-color: {c['divider']};
        border: 1px solid {c['border']};
        border-radius: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: {c['primary_surface']};
        color: {c['text_primary']};
    }}
    QHeaderView::section {{
        background-color: {c['bg_alt']};
        color: {c['text_primary']};
        font-weight: bold;
        padding: 6px;
        border: none;
        border-bottom: 2px solid {c['primary']};
        border-right: 1px solid {c['divider']};
    }}

    /* ---- Buttons (base) ---- */
    QPushButton {{
        background-color: {c['btn_secondary_bg']};
        color: {c['btn_secondary_text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['btn_secondary_hover']};
    }}
    QPushButton:pressed {{
        background-color: #AAAAAA;
    }}
    QPushButton:disabled {{
        background-color: {c['bg_alt']};
        color: {c['text_disabled']};
        border-color: {c['divider']};
    }}

    /* ---- Scroll Area ---- */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* ---- Text Edit (logs) ---- */
    QTextEdit {{
        background-color: {c['bg_base']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
    }}

    /* ---- ProgressBar ---- */
    QProgressBar {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        text-align: center;
        height: 22px;
        background-color: {c['bg_alt']};
    }}
    QProgressBar::chunk {{
        background-color: {c['primary']};
        border-radius: 3px;
    }}

    /* ---- Label informativo ---- */
    QLabel[role="info"] {{
        color: {c['text_secondary']};
        font-style: italic;
        font-size: 12px;
    }}

    /* ---- Splitter ---- */
    QSplitter::handle {{
        background-color: {c['divider']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    """


# ======================================================================
# Estilos para variantes de botones (aplicar vía setStyleSheet individual)
# ======================================================================

BUTTON_STYLES = {
    "primary": f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['primary_light']}; }}
        QPushButton:pressed {{ background-color: {COLORS['primary_dark']}; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "success": f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['success_light']}; }}
        QPushButton:pressed {{ background-color: #1B5E20; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "warning": f"""
        QPushButton {{
            background-color: {COLORS['warning']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['warning_light']}; }}
        QPushButton:pressed {{ background-color: #BF360C; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "secondary": f"""
        QPushButton {{
            background-color: {COLORS['btn_secondary_bg']};
            color: {COLORS['btn_secondary_text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ background-color: {COLORS['btn_secondary_hover']}; }}
        QPushButton:pressed {{ background-color: #AAAAAA; }}
    """,
}


# ======================================================================
# Función principal — aplicar tema a la app
# ======================================================================

def apply_theme(app: QApplication):
    """
    Aplica el tema visual completo a la aplicación.
    Llamar después de app.setStyle('Fusion').
    """
    # 1. QPalette base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS["bg_window"]))
    palette.setColor(QPalette.WindowText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Base, QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS["bg_alt"]))
    palette.setColor(QPalette.Text, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.PlaceholderText, QColor(COLORS["text_placeholder"]))
    palette.setColor(QPalette.Button, QColor(COLORS["btn_secondary_bg"]))
    palette.setColor(QPalette.ButtonText, QColor(COLORS["btn_secondary_text"]))
    palette.setColor(QPalette.Highlight, QColor(COLORS["primary"]))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipBase, QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.ToolTipText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Light, QColor("#FFFFFF"))
    palette.setColor(QPalette.Midlight, QColor(COLORS["bg_alt"]))
    palette.setColor(QPalette.Mid, QColor(COLORS["border"]))
    palette.setColor(QPalette.Dark, QColor(COLORS["text_secondary"]))

    app.setPalette(palette)

    # 2. Stylesheet global
    app.setStyleSheet(_build_stylesheet())
```

##### Step 1.2 Verification Checklist
- [ ] El archivo `themes.py` existe en la raíz del proyecto
- [ ] Test rápido en terminal:
  ```bash
  python -c "from PySide6.QtWidgets import QApplication; app = QApplication([]); app.setStyle('Fusion'); from themes import apply_theme; apply_theme(app); print('Tema aplicado OK')"
  ```
  Debe imprimir `Tema aplicado OK` sin errores

---

#### Step 1.3: Crear `gui_components.py` — Componentes GUI Reutilizables

- [ ] Crear el archivo `gui_components.py` en la raíz del proyecto
- [ ] Copiar y pegar el código siguiente en `gui_components.py`:

```python
"""
gui_components.py — Componentes GUI reutilizables para SAP2000 Automation Suite.

Provee widgets estandarizados:
- StyledButton: Botón con variantes de color (primary, success, warning, secondary)
- LogWidget: Área de log con auto-scroll y timestamp
- ProgressGroup: QGroupBox con QProgressBar + QLabel de estado
- ConnectionStatusWidget: Indicador visual de conexión SAP2000
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QPushButton, QGroupBox, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLabel, QTextEdit, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from themes import BUTTON_STYLES, COLORS


# ======================================================================
# StyledButton
# ======================================================================

class StyledButton(QPushButton):
    """
    QPushButton con estilo preconfigurado por variante.

    Variantes: 'primary', 'success', 'warning', 'secondary'

    Uso:
        btn = StyledButton("📥 Leer SAP2000", variant="primary")
    """

    def __init__(self, text: str = "", variant: str = "secondary", parent=None):
        super().__init__(text, parent)
        style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
        self.setStyleSheet(style)
        self._variant = variant

    def set_variant(self, variant: str):
        """Cambia la variante visual del botón."""
        style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
        self.setStyleSheet(style)
        self._variant = variant


# ======================================================================
# LogWidget
# ======================================================================

class LogWidget(QTextEdit):
    """
    Área de log de solo lectura con auto-scroll y formato de timestamp.

    Uso:
        log = LogWidget()
        log.log("Operación completada", level="SUCCESS")
    """

    _LEVEL_COLORS = {
        "INFO":    COLORS["text_secondary"],
        "SUCCESS": COLORS["success"],
        "WARNING": COLORS["warning"],
        "ERROR":   COLORS["error"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def log(self, message: str, level: str = "INFO"):
        """Agrega una línea al log con timestamp y color por nivel."""
        ts = datetime.now().strftime("%H:%M:%S")
        prefixes = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        prefix = prefixes.get(level, "")
        color = self._LEVEL_COLORS.get(level, COLORS["text_primary"])
        html = f'<span style="color:{color}">[{ts}] {prefix} {message}</span>'
        self.append(html)
        # Auto-scroll al final
        self.moveCursor(QTextCursor.End)

    def clear_log(self):
        """Limpia todo el contenido del log."""
        self.clear()


# ======================================================================
# ProgressGroup
# ======================================================================

class ProgressGroup(QGroupBox):
    """
    QGroupBox con QProgressBar y QLabel de estado.

    Uso:
        pg = ProgressGroup("Progreso")
        pg.set_progress(45, "Creando nudos...")
        pg.set_visible(True)
    """

    def __init__(self, title: str = "Progreso", parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-style: italic; font-size: 12px;"
        )
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setVisible(False)

    def set_progress(self, value: int, message: str = ""):
        """Actualiza la barra y el mensaje de estado."""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def reset(self):
        """Reinicia la barra y oculta el grupo."""
        self.progress_bar.setValue(0)
        self.status_label.setText("")
        self.setVisible(False)

    def set_visible(self, visible: bool):
        """Muestra u oculta el grupo de progreso."""
        self.setVisible(visible)


# ======================================================================
# ConnectionStatusWidget
# ======================================================================

class ConnectionStatusWidget(QWidget):
    """
    Indicador visual del estado de conexión con SAP2000.
    Muestra un punto de color + texto de estado.

    Uso:
        csw = ConnectionStatusWidget()
        csw.set_connected(True)   # Verde: "Conectado a SAP2000"
        csw.set_connected(False)  # Rojo: "Desconectado"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 2, 8, 2)

        self._indicator = QLabel("●")
        self._indicator.setFixedWidth(18)
        layout.addWidget(self._indicator)

        self._label = QLabel("Desconectado")
        layout.addWidget(self._label)

        self.setLayout(layout)
        self.set_connected(False)

    def set_connected(self, connected: bool):
        """Actualiza el indicador visual según el estado de conexión."""
        if connected:
            self._indicator.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 16px;"
            )
            self._label.setText("Conectado a SAP2000")
            self._label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        else:
            self._indicator.setStyleSheet(
                f"color: {COLORS['error']}; font-size: 16px;"
            )
            self._label.setText("Desconectado")
            self._label.setStyleSheet(f"color: {COLORS['text_secondary']};")
```

##### Step 1.3 Verification Checklist
- [ ] El archivo `gui_components.py` existe en la raíz del proyecto
- [ ] Test rápido en terminal:
  ```bash
  python -c "from PySide6.QtWidgets import QApplication; app = QApplication([]); from themes import apply_theme; apply_theme(app); from gui_components import StyledButton, LogWidget, ProgressGroup, ConnectionStatusWidget; print('Componentes importados OK')"
  ```
  Debe imprimir `Componentes importados OK` sin errores

---

#### Step 1.4: Crear `sap_utils_common.py` — Utilidades SAP API Compartidas

- [ ] Crear el archivo `sap_utils_common.py` en la raíz del proyecto
- [ ] Copiar y pegar el código siguiente en `sap_utils_common.py`:

```python
"""
sap_utils_common.py — Funciones utilitarias compartidas para la SAP2000 API.

Provee:
- check_ret_code(ret): Validador universal de retornos comtypes
- safe_sap_call(func, *args): Wrapper con manejo de errores automático
- get_materials_by_type(sap_model, mat_type): Extractor de materiales por tipo
- create_point_safe(sap_model, x, y, z, name): Creador de puntos con validación
"""

from typing import Any, Optional, Tuple, List

from app_logger import AppLogger


def check_ret_code(ret) -> bool:
    """
    Validador universal para retornos de la API SAP2000 vía comtypes.

    La API retorna TUPLAS donde el último elemento es el código de retorno.
    ret[-1] == 0 indica éxito.

    También maneja el caso donde la función retorna un entero directo.

    Args:
        ret: Resultado de una llamada a la API SAP2000. Puede ser:
             - tuple/list: ret[-1] es el código de retorno
             - int: el valor directo es el código de retorno

    Returns:
        True si el código de retorno indica éxito (0), False en caso contrario.
    """
    if ret is None:
        return False
    if isinstance(ret, (tuple, list)):
        return len(ret) > 0 and ret[-1] == 0
    if isinstance(ret, int):
        return ret == 0
    return False


def safe_sap_call(func, *args, default=None, description: str = ""):
    """
    Wrapper para llamadas a la API SAP2000 con manejo de errores automático.

    Args:
        func: Función/método de la API SAP2000 a ejecutar
        *args: Argumentos para la función
        default: Valor a retornar en caso de error
        description: Descripción legible de la operación (para logs)

    Returns:
        El resultado de la llamada si exitosa, o *default* si falla.
    """
    logger = AppLogger()
    try:
        ret = func(*args)
        if check_ret_code(ret):
            return ret
        else:
            if description:
                logger.warning(f"{description}: código de retorno indica fallo")
            return default
    except Exception as e:
        if description:
            logger.error(f"{description}: {e}")
        return default


def get_materials_by_type(sap_model, mat_type: int) -> List[str]:
    """
    Obtiene la lista de materiales filtrados por tipo desde SAP2000.

    Args:
        sap_model: Objeto SapModel conectado
        mat_type: Tipo de material según API SAP2000:
                  1 = Steel, 2 = Concrete, 3 = NoDesign,
                  4 = Aluminum, 5 = ColdFormed, 6 = Rebar

    Returns:
        Lista de nombres de materiales del tipo especificado.
    """
    if not sap_model:
        return []

    try:
        ret = sap_model.PropMaterial.GetNameList()
        if not check_ret_code(ret):
            return []

        count = ret[0]
        names = ret[1]

        if count == 0:
            return []

        # Normalizar: si count == 1, names puede ser str en vez de tuple
        if isinstance(names, str):
            names = (names,)

        result = []
        for name in names:
            try:
                type_ret = sap_model.PropMaterial.GetTypeOAPI(name)
                if check_ret_code(type_ret) and type_ret[0] == mat_type:
                    result.append(name)
            except Exception:
                continue

        return result

    except Exception:
        return []


def create_point_safe(
    sap_model, x: float, y: float, z: float, name: str = ""
) -> Optional[str]:
    """
    Crea un punto en SAP2000 con validación y manejo de errores.

    Args:
        sap_model: Objeto SapModel conectado
        x, y, z: Coordenadas del punto
        name: Nombre asignado al punto (vacío = autogenerado)

    Returns:
        Nombre del punto creado, o None si falla.
    """
    if not sap_model:
        return None

    logger = AppLogger()
    try:
        ret = sap_model.PointObj.AddCartesian(x, y, z, "", name, "Global")
        if check_ret_code(ret):
            return ret[0] if isinstance(ret, (tuple, list)) else name
        else:
            logger.warning(f"No se pudo crear punto ({x}, {y}, {z})")
            return None
    except Exception as e:
        logger.error(f"Error al crear punto ({x}, {y}, {z}): {e}")
        return None
```

##### Step 1.4 Verification Checklist
- [ ] El archivo `sap_utils_common.py` existe en la raíz del proyecto
- [ ] Test rápido en terminal:
  ```bash
  python -c "from sap_utils_common import check_ret_code; print(check_ret_code((5, ['a','b'], 0))); print(check_ret_code((5, ['a','b'], 1))); print(check_ret_code(0)); print(check_ret_code(1)); print(check_ret_code(None))"
  ```
  Debe imprimir:
  ```
  True
  False
  True
  False
  False
  ```

---

#### Step 1 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: add infrastructure base - themes, gui_components, sap_utils_common, app_logger
```

Archivos creados:
- `app_logger.py`
- `themes.py`
- `gui_components.py`
- `sap_utils_common.py`
