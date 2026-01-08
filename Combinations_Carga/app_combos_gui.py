import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QMessageBox, QLabel)
from PySide6.QtCore import Qt

# Importar backend
try:
    # Intento de import relativo (cuando funciona como paquete)
    from .combos_backend import ComboBackend
except ImportError:
    # Fallback para ejecución directa
    try:
        from combos_backend import ComboBackend
    except ImportError:
        sys.path.append(os.path.dirname(__file__))
        from combos_backend import ComboBackend

class CombosWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        
        # Si nos pasan la interfaz, usamos su modelo (puede ser None)
        # Si no, el backend intentará conectar por su cuenta
        model = self.sap_interface.SapModel if self.sap_interface else None
        self.backend = ComboBackend(sap_model=model)
        
        # Conectar señal si existe
        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)
            
        self.load_cases = [] # Lista de nombres de columnas dinámicas
        self.init_ui()

    def on_connection_changed(self, connected):
        """Actualizar el modelo del backend cuando la conexión global cambia."""
        if connected:
            self.backend.SapModel = self.sap_interface.SapModel
            self.lbl_info.setText("Conexión global recibida.")
        else:
            self.backend.SapModel = None
            self.lbl_info.setText("Conexión perdida.")
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Toolbar ---
        btn_layout = QHBoxLayout()
        
        self.btn_read = QPushButton("📥 Leer de SAP2000")
        self.btn_read.clicked.connect(self.load_from_sap)
        
        self.btn_send = QPushButton("📤 Enviar a SAP2000")
        self.btn_send.clicked.connect(self.send_to_sap)
        self.btn_send.setStyleSheet("background-color: #d4f0f0; font-weight: bold;")
        
        self.btn_add_row = QPushButton("➕ Agregar Fila")
        self.btn_add_row.clicked.connect(self.add_row)
        
        self.btn_del_row = QPushButton("➖ Eliminar Fila")
        self.btn_del_row.clicked.connect(self.delete_row)
        
        btn_layout.addWidget(self.btn_read)
        btn_layout.addWidget(self.btn_send)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_del_row)
        
        layout.addLayout(btn_layout)
        
        # --- Info Label ---
        self.lbl_info = QLabel("Conecta con SAP2000 para cargar los Load Cases y Combinaciones.")
        self.lbl_info.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_info)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3) # Inicialmente Nombre, Tipo, ASD/LRFD
        self.table.setHorizontalHeaderLabels(["Nombre Combinación", "Tipo", "ASD/LRFD"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def load_from_sap(self):
        self.lbl_info.setText("Conectando...")
        QApplication.processEvents()
        
        # 1. Obtener Load Cases (Columnas)
        cases = self.backend.get_load_cases()
        if not cases:
            self.lbl_info.setText("No se encontraron Load Cases o no hay conexión.")
            return
            
        self.load_cases = cases
        
        # Configurar columnas: Nombre, Tipo, ASD/LRFD, [Case1, Case2, ...]
        headers = ["Nombre Combinación", "Tipo", "ASD/LRFD"] + cases
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # 2. Obtener Combinaciones existentes (Filas)
        combos = self.backend.get_combinations()
        
        self.table.setRowCount(0)
        
        for c in combos:
            self.add_row_data(c['name'], c['type'], c['items'])
            
        self.lbl_info.setText(f"Cargados {len(cases)} Load Cases y {len(combos)} Combinaciones.")
        
    def add_row(self):
        self.add_row_data("COMB_N", 0, {})
        
    def delete_row(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            self.table.removeRow(row)
            
    def add_row_data(self, name, c_type, items):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Col 0: Nombre
        self.table.setItem(row, 0, QTableWidgetItem(str(name)))
        
        # Col 1: Tipo (ComboBox)
        combo_type = QComboBox()
        # Tipos según API: 0=Linear Additive, 1=Envelope, 2=Absolute Additive, 3=SRSS, 4=Range Additive
        types = ["Linear Additive", "Envelope", "Absolute Additive", "SRSS", "Range Additive"]
        combo_type.addItems(types)
        if 0 <= c_type < len(types):
            combo_type.setCurrentIndex(c_type)
        self.table.setCellWidget(row, 1, combo_type)
        
        # Col 2: ASD/LRFD (ComboBox)
        combo_design = QComboBox()
        design_opts = ["ASD", "LRFD", ""]
        combo_design.addItems(design_opts)
        combo_design.setCurrentIndex(2) # Default ""
        self.table.setCellWidget(row, 2, combo_design)

        # Col 3+: Factores
        for i, case_name in enumerate(self.load_cases):
            col_idx = 3 + i
            factor = items.get(case_name, "")
            if factor != "":
                factor = str(factor)
            
            item = QTableWidgetItem(factor)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col_idx, item)

    def send_to_sap(self):
        if not self.load_cases:
            QMessageBox.warning(self, "Error", "Primero debes leer los Load Cases de SAP2000.")
            return

        data_to_send = []
        rows = self.table.rowCount()
        
        for r in range(rows):
            # Nombre
            item_name = self.table.item(r, 0)
            name = item_name.text() if item_name else ""
            if not name: continue
            
            # Tipo
            widget_type = self.table.cellWidget(r, 1)
            c_type = widget_type.currentIndex() if widget_type else 0
            
            # Items (Factores)
            items = {}
            for i, case_name in enumerate(self.load_cases):
                col_idx = 3 + i
                item_factor = self.table.item(r, col_idx)
                text = item_factor.text() if item_factor else ""
                
                if text.strip():
                    try:
                        val = float(text)
                        if val != 0:
                            items[case_name] = val
                    except ValueError:
                        pass # Ignorar valores no numéricos
            
            data_to_send.append({
                'name': name,
                'type': c_type,
                'items': items
            })
            
        if not data_to_send:
            QMessageBox.information(self, "Info", "No hay datos válidos para enviar.")
            return
            
        count = self.backend.push_combinations(data_to_send)
        QMessageBox.information(self, "Éxito", f"Se procesaron {count} combinaciones en SAP2000.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Combinaciones de Carga")
        self.resize(800, 500)
        self.setCentralWidget(CombosWidget())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
