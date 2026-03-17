import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox,
    QWidget, QLabel, QToolBar, QMenuBar,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import QSettings, Qt
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
    from Fundaciones.fundaciones_gui import FundacionesWidget
except ImportError as e:
    print(f"Error importing modules: {e}")
    class CombosWidget(QWidget): pass
    class MeshUtilsWidget(QWidget): pass
    class BasePlateWidget(QWidget): pass
    class ModeloBaseWidget(QWidget): pass
    class FundacionesWidget(QWidget): pass


class UnifiedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAP2000 Automation Suite")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)
        self.logger = AppLogger()
        self._settings = QSettings("SAPy2000", "UnifiedApp")

        # --- SAP Interface ---
        self.sap_interface = SapInterface()
        self.sap_interface.connectionChanged.connect(self.on_connection_changed)

        # --- Menu Bar ---
        self._create_menus()

        # --- Toolbar ---
        toolbar = QToolBar("Connection")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.btn_connect = StyledButton("Conectar a SAP2000", variant="primary")
        self.btn_connect.clicked.connect(self.sap_interface.connect_to_sap)
        toolbar.addWidget(self.btn_connect)

        # --- Connection Status en status bar ---
        self.conn_status = ConnectionStatusWidget()
        self.statusBar().addPermanentWidget(self.conn_status)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_tabs()
        self._restore_geometry()
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

    def _restore_geometry(self):
        """Restaura tamaño y estado de ventana guardados."""
        geometry = self._settings.value("geometry")
        state = self._settings.value("windowState")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """Guarda geometría antes de cerrar."""
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def changeEvent(self, event):
        """Fuerza actualización del layout al restaurar desde minimizado."""
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            if not (self.windowState() & Qt.WindowMinimized):
                self.centralWidget().updateGeometry()

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

        # Tab 5: Fundaciones
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