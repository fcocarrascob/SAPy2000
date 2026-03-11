# Step 2: Migración Módulo Central — main_app.py y sap_interface.py

## Goal
Aplicar el nuevo sistema de temas a la ventana principal, agregar `ConnectionStatusWidget` en la barra de estado, integrar logging y agregar menú "Acerca de".

## Prerequisites
- Step 1 completado y commiteado (archivos `themes.py`, `gui_components.py`, `sap_utils_common.py`, `app_logger.py` disponibles)
- Branch: `feature/standardization-gui-ux`

---

### Step-by-Step Instructions

#### Step 2.1: Actualizar `main_app.py` — Integrar Tema y Componentes

- [ ] Reemplazar el contenido completo de `main_app.py` con el código siguiente:

```python
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox,
    QWidget, QLabel, QToolBar, QMenuBar,
)
from PySide6.QtGui import QAction
from sap_interface import SapInterface
from themes import apply_theme
from gui_components import ConnectionStatusWidget, StyledButton
from app_logger import AppLogger

# Import modules as packages
try:
    from Combinations_Carga.app_combos_gui import CombosWidget
    from Utilidades_MOD.app_utils_gui import MeshUtilsWidget
    from Placa_Base.app_placabase_gui import BasePlateWidget
    from Modelo_Base.app_modelo_base_gui import ModeloBaseWidget
    from Reportes.report_gui import ReportWidget
    from Fundaciones.fundaciones_gui import FundacionesWidget
except ImportError as e:
    print(f"Error importing modules: {e}")
    class CombosWidget(QWidget): pass
    class MeshUtilsWidget(QWidget): pass
    class BasePlateWidget(QWidget): pass
    class ModeloBaseWidget(QWidget): pass
    class ReportWidget(QWidget): pass
    class FundacionesWidget(QWidget): pass


class UnifiedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAP2000 Automation Suite")
        self.resize(1024, 768)
        self.logger = AppLogger()

        # --- SAP Interface ---
        self.sap_interface = SapInterface()
        self.sap_interface.connectionChanged.connect(self.on_connection_changed)

        # --- Menu Bar ---
        self._create_menus()

        # --- Toolbar ---
        toolbar = QToolBar("Connection")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.btn_connect = StyledButton("🔌 Conectar a SAP2000", variant="primary")
        self.btn_connect.clicked.connect(self.sap_interface.connect_to_sap)
        toolbar.addWidget(self.btn_connect)

        # --- Connection Status en status bar ---
        self.conn_status = ConnectionStatusWidget()
        self.statusBar().addPermanentWidget(self.conn_status)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_tabs()
        self.logger.info("Aplicación iniciada")

    def _create_menus(self):
        """Crea la barra de menú con opciones de la aplicación."""
        menu_bar = self.menuBar()

        # Menú Ver
        menu_ver = menu_bar.addMenu("Ver")

        action_export_log = QAction("Exportar Logs...", self)
        action_export_log.triggered.connect(self._export_logs)
        menu_ver.addAction(action_export_log)

        # Menú Ayuda
        menu_ayuda = menu_bar.addMenu("Ayuda")

        action_about = QAction("Acerca de", self)
        action_about.triggered.connect(self._show_about)
        menu_ayuda.addAction(action_about)

    def _export_logs(self):
        """Exporta el log a un archivo de texto."""
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Logs", "sapy2000_log.txt", "Archivos de texto (*.txt)"
        )
        if path:
            if self.logger.export_to_file(path):
                QMessageBox.information(self, "Exportar Logs", f"Log exportado a:\n{path}")
            else:
                QMessageBox.warning(self, "Error", "No se pudo exportar el log.")

    def _show_about(self):
        """Muestra el diálogo Acerca de."""
        QMessageBox.about(
            self,
            "Acerca de SAP2000 Automation Suite",
            "<h3>SAP2000 Automation Suite</h3>"
            "<p>Herramienta de automatización para CSI SAP2000.</p>"
            "<p>Automatiza creación de modelos, combinaciones de carga, "
            "diseño de placas base, fundaciones y más.</p>"
            "<hr>"
            "<p><b>Tecnologías:</b> Python · PySide6 · comtypes · SAP2000 OAPI</p>"
            "<p><b>Normativa:</b> NCh2369:2025 · AISC 360</p>"
        )

    def on_connection_changed(self, connected):
        self.conn_status.set_connected(connected)
        if connected:
            self.btn_connect.setEnabled(False)
            self.btn_connect.setText("✅ Conectado")
            self.logger.success("Conexión establecida con SAP2000")
        else:
            self.btn_connect.setEnabled(True)
            self.btn_connect.setText("🔌 Conectar a SAP2000")
            self.logger.warning("Desconectado de SAP2000")

    def init_tabs(self):
        # Tab 1: Combinations
        try:
            self.combos_tab = CombosWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.combos_tab, "Combinaciones de Carga")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Combinations: {e}"), "Combinaciones (Error)")

        # Tab 2: Utilities
        try:
            self.utils_tab = MeshUtilsWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.utils_tab, "Utilidades de Modelado")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Utilities: {e}"), "Utilidades (Error)")

        # Tab 3: Base Plate
        try:
            self.plate_tab = BasePlateWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.plate_tab, "Diseño Placa Base")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Base Plate: {e}"), "Placa Base (Error)")

        # Tab 4: Modelo Base
        try:
            self.base_model_tab = ModeloBaseWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.base_model_tab, "Modelo Base")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Base Model: {e}"), "Modelo Base (Error)")

        # Tab 5: Reportes
        try:
            self.reports_tab = ReportWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.reports_tab, "Memorias (Word)")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Reports: {e}"), "Reportes (Error)")

        # Tab 6: Fundaciones
        try:
            self.fundaciones_tab = FundacionesWidget(sap_interface=self.sap_interface)
            self.tabs.addTab(self.fundaciones_tab, "Fundaciones")
        except Exception as e:
            self.tabs.addTab(QLabel(f"Error loading Fundaciones: {e}"), "Fundaciones (Error)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)

    window = UnifiedApp()
    window.show()
    sys.exit(app.exec())
```

##### Step 2.1 Verification Checklist
- [ ] No errores de importación al ejecutar `python -m main_app`
- [ ] La ventana principal muestra el tema visual con colores profesionales
- [ ] La barra de estado contiene el indicador de conexión con punto rojo "Desconectado"
- [ ] El toolbar tiene el botón "🔌 Conectar a SAP2000" con estilo primary (azul)
- [ ] Menú "Ver" contiene "Exportar Logs..."
- [ ] Menú "Ayuda" contiene "Acerca de" y muestra un diálogo con información

---

#### Step 2.2: Actualizar `sap_interface.py` — Integrar Logger

- [ ] Reemplazar el contenido completo de `sap_interface.py` con el código siguiente:

```python
import sys
import comtypes.client
from PySide6.QtCore import QObject, Signal
from app_logger import AppLogger


class SapInterface(QObject):
    """
    Gestiona la conexión única con la API de SAP2000.
    Emite señales cuando el estado de la conexión cambia.
    """
    connectionChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self.SapModel = None
        self.SapObject = None
        self.logger = AppLogger()

    def connect_to_sap(self):
        """Intenta conectar a una instancia activa de SAP2000."""
        try:
            self.logger.info("Intentando conectar a SAP2000...")
            self.SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            self.SapModel = self.SapObject.SapModel

            # Verificar conexión con llamada simple
            self.SapModel.GetModelFilename()

            self.logger.success("Conexión exitosa con SAP2000")
            self.connectionChanged.emit(True)
            return True
        except Exception as e:
            self.logger.error(f"No se pudo conectar a SAP2000: {e}")
            self.SapModel = None
            self.SapObject = None
            self.connectionChanged.emit(False)
            return False

    def disconnect(self):
        """Limpia la referencia a la conexión."""
        self.SapModel = None
        self.SapObject = None
        self.connectionChanged.emit(False)
        self.logger.info("Desconectado de SAP2000")

    def reconnect(self):
        """Intenta reconectar a SAP2000 (útil si se pierde la conexión)."""
        self.logger.info("Intentando reconectar...")
        self.SapModel = None
        self.SapObject = None
        return self.connect_to_sap()

    def is_connected(self):
        return self.SapModel is not None
```

##### Step 2.2 Verification Checklist
- [ ] Sin errores de importación al ejecutar `python -c "from sap_interface import SapInterface; print('OK')"`
- [ ] El `SapInterface` ahora tiene método `reconnect()`
- [ ] Los mensajes de conexión se log-ean con formato de timestamp vía `AppLogger`

---

#### Step 2 STOP & COMMIT

**STOP & COMMIT:** Agent must stop here and wait for the user to test, stage, and commit the change.

Commit sugerido:
```
feat: apply theme and connection status to main_app, integrate logger in sap_interface
```

Archivos modificados:
- `main_app.py`
- `sap_interface.py`
