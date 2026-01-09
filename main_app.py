import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox, QWidget, QLabel, QToolBar
from PySide6.QtGui import QAction
from sap_interface import SapInterface

# Import modules as packages
try:
    from Combinations_Carga.app_combos_gui import CombosWidget
    from Utilidades_MOD.app_utils_gui import MeshUtilsWidget
    from Placa_Base.app_placabase_gui import BasePlateWidget
    from Modelo_Base.app_modelo_base_gui import ModeloBaseWidget
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Fallback to empty classes to allow app to start and show error
    class CombosWidget(QWidget): pass
    class MeshUtilsWidget(QWidget): pass
    class BasePlateWidget(QWidget): pass
    class ModeloBaseWidget(QWidget): pass


class UnifiedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAP2000 Automation Suite")
        self.resize(1024, 768)
        
        # --- SAP Interface ---
        self.sap_interface = SapInterface()
        self.sap_interface.connectionChanged.connect(self.on_connection_changed)
        
        # --- Toolbar ---
        toolbar = QToolBar("Connection")
        self.addToolBar(toolbar)
        
        self.action_connect = QAction("🔌 Conectar a SAP2000", self)
        self.action_connect.triggered.connect(self.sap_interface.connect_to_sap)
        toolbar.addAction(self.action_connect)
        
        self.status_label = QLabel("Estado: Desconectado 🔴  ")
        self.statusBar().addPermanentWidget(self.status_label)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.init_tabs()
        
    def on_connection_changed(self, connected):
        if connected:
            self.status_label.setText("Estado: Conectado ✅  ")
            self.action_connect.setEnabled(False)
            self.action_connect.setText("Conectado")
        else:
            self.status_label.setText("Estado: Desconectado 🔴  ")
            self.action_connect.setEnabled(True)
            self.action_connect.setText("🔌 Conectar a SAP2000")

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
            self.tabs.addTab(self.utils_tab, "Utilidades de Mallado")
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Set a global style or palette here
    app.setStyle("Fusion")
    
    window = UnifiedApp()
    window.show()
    sys.exit(app.exec())
