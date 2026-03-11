"""GUI de Combinaciones de Carga — Widget para gestionar combos en SAP2000."""

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from .combos_backend import ComboBackend
except ImportError:
    try:
        from combos_backend import ComboBackend
    except ImportError:
        sys.path.append(os.path.dirname(__file__))
        from combos_backend import ComboBackend

from gui_components import StyledButton, LogWidget
from themes import COLORS


class CombosWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface

        model = self.sap_interface.SapModel if self.sap_interface else None
        self.backend = ComboBackend(sap_model=model)

        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)

        self.load_cases = []
        self.init_ui()

    def on_connection_changed(self, connected):
        """Actualizar el modelo del backend cuando la conexión global cambia."""
        if connected:
            self.backend.SapModel = self.sap_interface.SapModel
            self.log.log("Conexión global recibida", level="SUCCESS")
        else:
            self.backend.SapModel = None
            self.log.log("Conexión perdida", level="WARNING")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- Toolbar ---
        btn_layout = QHBoxLayout()

        self.btn_read = StyledButton("📥 Leer de SAP2000", variant="primary")
        self.btn_read.clicked.connect(self.load_from_sap)

        self.btn_send = StyledButton("📤 Enviar a SAP2000", variant="success")
        self.btn_send.clicked.connect(self.send_to_sap)

        self.btn_add_row = StyledButton("➕ Agregar Fila", variant="secondary")
        self.btn_add_row.clicked.connect(self.add_row)

        self.btn_del_row = StyledButton("➖ Eliminar Fila", variant="secondary")
        self.btn_del_row.clicked.connect(self.delete_row)

        btn_layout.addWidget(self.btn_read)
        btn_layout.addWidget(self.btn_send)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_row)
        btn_layout.addWidget(self.btn_del_row)

        layout.addLayout(btn_layout)

        # --- Info Label ---
        self.lbl_info = QLabel("Conecta con SAP2000 para cargar los Load Cases y Combinaciones.")
        self.lbl_info.setProperty("role", "info")
        layout.addWidget(self.lbl_info)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre Combinación", "Tipo", "ASD/LRFD"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # --- Log ---
        self.log = LogWidget()
        layout.addWidget(self.log)

        self.setLayout(layout)

    def load_from_sap(self):
        self.lbl_info.setText("Conectando...")
        QApplication.processEvents()

        cases = self.backend.get_load_cases()
        if not cases:
            self.lbl_info.setText("No se encontraron Load Cases o no hay conexión.")
            self.log.log("No se encontraron Load Cases", level="WARNING")
            return

        self.load_cases = cases

        headers = ["Nombre Combinación", "Tipo", "ASD/LRFD"] + cases
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        combos = self.backend.get_combinations()
        self.table.setRowCount(0)

        for c in combos:
            self.add_row_data(c["name"], c["type"], c["items"])

        msg = f"Cargados {len(cases)} Load Cases y {len(combos)} Combinaciones."
        self.lbl_info.setText(msg)
        self.log.log(msg, level="SUCCESS")

    def add_row(self):
        self.add_row_data("COMB_N", 0, {})

    def delete_row(self):
        rows = sorted(
            set(index.row() for index in self.table.selectedIndexes()), reverse=True
        )
        for row in rows:
            self.table.removeRow(row)

    def add_row_data(self, name, c_type, items):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Col 0: Nombre
        self.table.setItem(row, 0, QTableWidgetItem(str(name)))

        # Col 1: Tipo (ComboBox)
        combo_type = QComboBox()
        types = [
            "Linear Additive",
            "Envelope",
            "Absolute Additive",
            "SRSS",
            "Range Additive",
        ]
        combo_type.addItems(types)
        if 0 <= c_type < len(types):
            combo_type.setCurrentIndex(c_type)
        self.table.setCellWidget(row, 1, combo_type)

        # Col 2: ASD/LRFD (ComboBox)
        combo_design = QComboBox()
        design_opts = ["ASD", "LRFD", ""]
        combo_design.addItems(design_opts)
        combo_design.setCurrentIndex(2)
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
            QMessageBox.warning(
                self, "Error", "Primero debes leer los Load Cases de SAP2000."
            )
            return

        data_to_send = []
        rows = self.table.rowCount()

        for r in range(rows):
            item_name = self.table.item(r, 0)
            name = item_name.text() if item_name else ""
            if not name:
                continue

            widget_type = self.table.cellWidget(r, 1)
            c_type = widget_type.currentIndex() if widget_type else 0

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
                        pass

            data_to_send.append({"name": name, "type": c_type, "items": items})

        if not data_to_send:
            QMessageBox.information(self, "Info", "No hay datos válidos para enviar.")
            return

        count = self.backend.push_combinations(data_to_send)
        self.log.log(f"Se procesaron {count} combinaciones en SAP2000", level="SUCCESS")
        QMessageBox.information(
            self, "Éxito", f"Se procesaron {count} combinaciones en SAP2000."
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor de Combinaciones de Carga")
        self.resize(800, 500)
        self.setCentralWidget(CombosWidget())


if __name__ == "__main__":
    from themes import apply_theme

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())