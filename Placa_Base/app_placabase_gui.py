import sys
import os
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
                               QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox,
                               QTableWidget, QTableWidgetItem)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import QSize, QRectF
from PySide6.QtCore import QProcess, Qt

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'placabase_ARA.py')
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'placabase_ARA_config.json')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Placa Base - GUI (placabase_ARA)')

        # ComboBox con diámetros comunes y su equivalente en pulgadas
        self.bolt_combo = QComboBox()
        # (display, mm_value)
        dia_items = [
            ('16 mm (5/8\")', 16),
            ('19 mm (3/4\")', 19),
            ('22 mm (7/8\")', 22),
            ('25 mm (1\")', 25),
            ('32 mm (1 1/4\")', 32),
            ('38 mm (1 1/2\")', 38),
            ('44 mm (1 3/4\")', 44),
            ('51 mm (2\")', 51),
            ('57 mm (2 1/4\")', 57),
            ('64 mm (2 1/2\")', 64),
        ]
        for label, mm in dia_items:
            self.bolt_combo.addItem(label, mm)
        self.hcol_edit = QLineEdit('300.0')
        self.bcol_edit = QLineEdit('250.0')
        # nuevos campos: espesor de ala (flange) y alma (web) en mm
        self.flange_edit = QLineEdit('')
        self.web_edit = QLineEdit('')
        self.A_display = QLineEdit('100')
        self.A_display.setReadOnly(True)
        self.B_display = QLineEdit('100')
        self.B_display.setReadOnly(True)

        # Centers: tabla editable con columnas X, Y, Z
        self.centers_table = QTableWidget(0, 3)
        self.centers_table.setHorizontalHeaderLabels(['X', 'Y', 'Z'])
        self.centers_table.horizontalHeader().setStretchLastSection(True)
        self.add_row_btn = QPushButton('Agregar fila')
        self.remove_row_btn = QPushButton('Eliminar fila')
        self.add_row_btn.clicked.connect(self.add_row)
        self.remove_row_btn.clicked.connect(self.remove_selected_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.save_btn = QPushButton('Guardar config')
        self.run_btn = QPushButton('Guardar y Ejecutar')

        self.save_btn.clicked.connect(self.save_config)
        self.run_btn.clicked.connect(self.run_script)

        form_layout = QVBoxLayout()
        row = QHBoxLayout(); row.addWidget(QLabel('Diámetro perno:')); row.addWidget(self.bolt_combo)
        row.addWidget(QLabel('  A:')); row.addWidget(self.A_display)
        row.addWidget(QLabel('B:')); row.addWidget(self.B_display)
        form_layout.addLayout(row)
        row2 = QHBoxLayout(); row2.addWidget(QLabel('Alto columna H_col (mm):')); row2.addWidget(self.hcol_edit)
        form_layout.addLayout(row2)
        row3 = QHBoxLayout(); row3.addWidget(QLabel('Ancho columna B_col (mm):')); row3.addWidget(self.bcol_edit)
        # fila para espesores
        row_th = QHBoxLayout(); row_th.addWidget(QLabel('Espesor ala (mm):')); row_th.addWidget(self.flange_edit)
        row_th.addWidget(QLabel('Espesor alma (mm):')); row_th.addWidget(self.web_edit)
        form_layout.addLayout(row_th)
        form_layout.addLayout(row3)
        form_layout.addLayout(row3)
        form_layout.addWidget(QLabel('Centros de pernos (tabla X,Y,Z en mm):'))
        form_layout.addWidget(self.centers_table)
        row_btns = QHBoxLayout(); row_btns.addWidget(self.add_row_btn); row_btns.addWidget(self.remove_row_btn)
        form_layout.addLayout(row_btns)

        btn_row = QHBoxLayout(); btn_row.addWidget(self.save_btn); btn_row.addWidget(self.run_btn)
        form_layout.addLayout(btn_row)
        form_layout.addWidget(QLabel('Salida / Log:'))
        form_layout.addWidget(self.log)

        container = QWidget()
        # crear preview a la derecha
        self.preview = PreviewWidget(self)

        main_layout = QHBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(form_layout)
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(self.preview, 1)

        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.process = None

        # load existing config if present
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as fh:
                    cfg = json.load(fh)
                # seleccionar en combo el diámetro si existe en config
                cfg_dia = cfg.get('bolt_dia')
                if cfg_dia is not None:
                    # buscar índice con userData == cfg_dia
                    found_idx = -1
                    for i in range(self.bolt_combo.count()):
                        if float(self.bolt_combo.itemData(i)) == float(cfg_dia):
                            found_idx = i
                            break
                    if found_idx >= 0:
                        self.bolt_combo.setCurrentIndex(found_idx)
                # si no hay centros en config, insertar una fila vacía por defecto
                if not cfg.get('bolt_centers'):
                    self.add_row()
                
                self.hcol_edit.setText(str(cfg.get('H_col', self.hcol_edit.text())))
                self.bcol_edit.setText(str(cfg.get('B_col', self.bcol_edit.text())))
                # cargar espesores si vienen en la config
                if 'flange_thickness' in cfg:
                    try:
                        self.flange_edit.setText(str(cfg.get('flange_thickness', '')))
                    except Exception:
                        pass
                if 'web_thickness' in cfg:
                    try:
                        self.web_edit.setText(str(cfg.get('web_thickness', '')))
                    except Exception:
                        pass
                centers = cfg.get('bolt_centers')
                if centers:
                    # llenar tabla
                    self.centers_table.setRowCount(0)
                    for c in centers:
                        r = self.centers_table.rowCount()
                        self.centers_table.insertRow(r)
                        self.centers_table.setItem(r, 0, QTableWidgetItem(str(c[0])))
                        self.centers_table.setItem(r, 1, QTableWidgetItem(str(c[1])))
                        self.centers_table.setItem(r, 2, QTableWidgetItem(str(c[2] if len(c) > 2 else 0.0)))
            except Exception as e:
                self.log.append(f'No se pudo leer config existente: {e}')
            except Exception as e:
                self.log.append(f'No se pudo leer config existente: {e}')

        # actualizar A/B según bolt_dia inicial
        self.update_A_B_display()

        # actualizar valores por defecto de espesores según H/B
        def update_thickness_defaults():
            try:
                H = float(self.hcol_edit.text())
            except Exception:
                H = 300.0
            try:
                B = float(self.bcol_edit.text())
            except Exception:
                B = 250.0
            # si campos vacíos, asignar valores estimados
            if not self.flange_edit.text().strip():
                self.flange_edit.setText(str(max(1.0, round(0.12 * H, 3))))
            if not self.web_edit.text().strip():
                self.web_edit.setText(str(max(1.0, round(0.08 * B, 3))))
        update_thickness_defaults()

        # conectar cambio de selección del combo para actualizar A/B y refrescar preview
        self.bolt_combo.currentIndexChanged.connect(self.update_A_B_display)
        self.bolt_combo.currentIndexChanged.connect(lambda *_: self.preview.update())
        # conectar cambios para refrescar preview (usar lambda para ignorar argumentos del signal)
        self.hcol_edit.textChanged.connect(lambda *_: self.preview.update())
        self.bcol_edit.textChanged.connect(lambda *_: self.preview.update())
        # también conectar editingFinished para asegurar actualización al terminar edición
        self.hcol_edit.editingFinished.connect(self.preview.update)
        self.bcol_edit.editingFinished.connect(self.preview.update)
        # conectar cambios H/B para recalcular espesores por defecto
        self.hcol_edit.textChanged.connect(lambda *_: update_thickness_defaults())
        self.bcol_edit.textChanged.connect(lambda *_: update_thickness_defaults())
        # conectar cambios en los campos de espesor para refrescar preview
        self.flange_edit.textChanged.connect(lambda *_: self.preview.update())
        self.web_edit.textChanged.connect(lambda *_: self.preview.update())
        # conectar cambios en la tabla (itemChanged y cellChanged por seguridad)
        self.centers_table.itemChanged.connect(lambda *_: self.preview.update())
        self.centers_table.cellChanged.connect(lambda r, c: self.preview.update())

        # asegurarse de que la preview refleje la configuración cargada inicialmente
        self.preview.update()

    def save_config(self):
        try:
            bolt_dia = float(self.bolt_combo.currentData())
            H_col = float(self.hcol_edit.text())
            B_col = float(self.bcol_edit.text())
        except ValueError:
            QMessageBox.warning(self, 'Error', 'Valores numéricos inválidos.')
            return False

        centers = []
        # leer filas de la tabla
        for r in range(self.centers_table.rowCount()):
            try:
                itx = self.centers_table.item(r, 0)
                ity = self.centers_table.item(r, 1)
                itz = self.centers_table.item(r, 2)
                if itx is None or ity is None:
                    QMessageBox.warning(self, 'Error', f'Fila {r+1} incompleta')
                    return False
                x = float(itx.text())
                y = float(ity.text())
                z = float(itz.text()) if itz is not None and itz.text().strip() != '' else 0.0
            except ValueError:
                QMessageBox.warning(self, 'Error', f'Valores inválidos en fila {r+1}')
                return False
            centers.append([x, y, z])

        cfg = {
            'bolt_dia': bolt_dia,
            'H_col': H_col,
            'B_col': B_col,
            'bolt_centers': centers,
            'flange_thickness': float(self.flange_edit.text()) if self.flange_edit.text().strip() != '' else None,
            'web_thickness': float(self.web_edit.text()) if self.web_edit.text().strip() != '' else None
        }
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as fh:
                json.dump(cfg, fh, indent=2)
            self.log.append(f'Config guardada en {CONFIG_PATH}')
            # actualizar A/B tras guardar
            self.update_A_B_display()
            self.preview.update()
            return True
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo guardar config: {e}')
            return False

    def run_script(self):
        ok = self.save_config()
        if not ok:
            return
        if not os.path.exists(SCRIPT_PATH):
            QMessageBox.critical(self, 'Error', f'No se encontró {SCRIPT_PATH}')
            return

        if self.process is not None and self.process.state() != QProcess.NotRunning:
            QMessageBox.information(self, 'Info', 'Ya hay un proceso en ejecución.')
            return

        self.log.append('Iniciando placabase_ARA.py...')
        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments([SCRIPT_PATH])
        self.process.setWorkingDirectory(os.path.dirname(SCRIPT_PATH))
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.start()

    def _read_stdout(self):
        data = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
        self.log.append(data)

    def _read_stderr(self):
        data = bytes(self.process.readAllStandardError()).decode('utf-8', errors='replace')
        self.log.append(data)

    def _on_finished(self, exitCode, exitStatus):
        self.log.append(f'Proceso terminado (exit {exitCode})')

    def add_row(self):
        r = self.centers_table.rowCount()
        self.centers_table.insertRow(r)
        # insertar celdas vacías
        self.centers_table.setItem(r, 0, QTableWidgetItem('0.0'))
        self.centers_table.setItem(r, 1, QTableWidgetItem('0.0'))
        self.centers_table.setItem(r, 2, QTableWidgetItem('0.0'))
        self.preview.update()

    def remove_selected_row(self):
        sel = self.centers_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, 'Info', 'Seleccione una fila para eliminar')
            return
        # eliminar desde la última para mantener índices
        rows = sorted([s.row() for s in sel], reverse=True)
        for r in rows:
            self.centers_table.removeRow(r)
        self.preview.update()

    def get_A_B_from_dia(self, dia):
        """Mapea `dia` (mm) a A,B según tabla aproximada usada en scripts."""
        try:
            # dia puede venir como dato de combo (int) o texto
            d = int(round(float(dia)))
        except Exception:
            return 100, 100
        mapping = {
            16: (80, 80),
            19: (100, 100),
            22: (100, 100),
            25: (100, 100),
            32: (125, 125),
            38: (150, 150),
            44: (175, 175),
            51: (200, 200),
            57: (225, 225),
            64: (250, 250),
        }
        return mapping.get(d, (100, 100))

    def update_A_B_display(self, *args):
        """Actualizar campos A/B. Acepta argumentos opcionales del signal."""
        # obtener dato desde el combo (userData) o fallback al texto del item
        try:
            data = self.bolt_combo.currentData()
            if data is None:
                # intentar parsear texto entre números
                text = self.bolt_combo.currentText()
                # buscar primer número en el string
                import re
                m = re.search(r"(\d+(?:\.\d+)?)", text)
                dia_val = float(m.group(1)) if m else 100.0
            else:
                dia_val = float(data)
        except Exception:
            dia_val = 100.0
        A, B = self.get_A_B_from_dia(dia_val)
        self.A_display.setText(str(A))
        self.B_display.setText(str(B))


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(QSize(300, 300))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor(255, 255, 255))

        # locate the MainWindow ancestor which holds form widgets (hcol_edit, bcol_edit, centers_table)
        parent = self.parent()
        while parent is not None and not hasattr(parent, 'hcol_edit'):
            parent = parent.parent()
        if parent is None:
            return
        # leer H_col y B_col
        try:
            H = float(parent.hcol_edit.text())
        except Exception:
            H = 300.0
        try:
            B = float(parent.bcol_edit.text())
        except Exception:
            B = 250.0

        # obtener pernos desde la tabla
        centers = []
        try:
            for r in range(parent.centers_table.rowCount()):
                itx = parent.centers_table.item(r, 0)
                ity = parent.centers_table.item(r, 1)
                itz = parent.centers_table.item(r, 2)
                if itx and ity:
                    cx = float(itx.text())
                    cy = float(ity.text())
                    cz = float(itz.text()) if itz and itz.text().strip() != '' else 0.0
                    centers.append((cx, cy, cz))
        except Exception:
            centers = []

        # compute scale to fit B x H and bolt extents inside widget with margin
        w = rect.width()
        h = rect.height()
        margin = 20
        avail_w = max(10, w - 2 * margin)
        avail_h = max(10, h - 2 * margin)
        # determine extents from bolt coordinates (mm)
        max_abs_bx = 0.0
        max_abs_by = 0.0
        for (bx, by, bz) in centers:
            try:
                max_abs_bx = max(max_abs_bx, abs(float(bx)))
                max_abs_by = max(max_abs_by, abs(float(by)))
            except Exception:
                continue
        # small buffer in mm so bolts near the border remain visible
        buffer_mm = 10.0
        required_half_w_mm = max(B / 2.0, max_abs_bx + buffer_mm)
        required_half_h_mm = max(H / 2.0, max_abs_by + buffer_mm)
        # map mm -> pixels: content width = 2 * required_half_mm
        scale = min(avail_w / (2.0 * required_half_w_mm if required_half_w_mm > 0 else 1.0),
                    avail_h / (2.0 * required_half_h_mm if required_half_h_mm > 0 else 1.0))
        # center in widget
        cx0 = rect.left() + w / 2
        cy0 = rect.top() + h / 2

        # Draw I-section (W profile) centered at cx0,cy0
        # Usar espesores proporcionados por el usuario si están presentes,
        # sino caer a estimaciones por proporción de H/B
        try:
            flange_thickness = max(1.0, float(parent.flange_edit.text()))
        except Exception:
            flange_thickness = max(1.0, 0.12 * H)
        try:
            web_thickness = max(1.0, float(parent.web_edit.text()))
        except Exception:
            web_thickness = max(1.0, 0.08 * B)

        half_w_px = (B / 2.0) * scale
        half_h_px = (H / 2.0) * scale

        flange_h_px = flange_thickness * scale
        web_w_px = max(2.0, web_thickness * scale)

        # Top flange rectangle
        top_rect = QRectF(cx0 - half_w_px, cy0 - half_h_px, 2 * half_w_px, flange_h_px)
        # Bottom flange rectangle
        bottom_rect = QRectF(cx0 - half_w_px, cy0 + half_h_px - flange_h_px, 2 * half_w_px, flange_h_px)
        # Web rectangle (between flanges)
        web_rect = QRectF(cx0 - web_w_px/2.0, cy0 - half_h_px + flange_h_px, web_w_px, 2 * half_h_px - 2 * flange_h_px)

        pen = QPen(QColor(200, 30, 30), max(1.0, scale * 0.5))
        brush = QBrush(QColor(255, 255, 255, 0))
        painter.setPen(pen)
        painter.setBrush(brush)
        # draw flanges and web outline (red lines)
        painter.drawRect(top_rect)
        painter.drawRect(bottom_rect)
        painter.drawRect(web_rect)

        # draw center cross (optional)
        painter.setPen(QPen(QColor(0, 150, 200), 1))
        painter.drawLine(cx0 - 10, cy0, cx0 + 10, cy0)
        painter.drawLine(cx0, cy0 - 10, cx0, cy0 + 10)

        # draw bolts as small circles
        bolt_radius_px = max(3, int(4 * scale))
        painter.setBrush(QBrush(QColor(200, 30, 30)))
        painter.setPen(QPen(QColor(120, 20, 20), 1))
        for (bx, by, bz) in centers:
            # treat bx,by as mm relative to column center
            px = cx0 + bx * scale
            py = cy0 - by * scale  # invert y for screen coords
            painter.drawEllipse(px - bolt_radius_px, py - bolt_radius_px, bolt_radius_px * 2, bolt_radius_px * 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(700, 600)
    w.show()
    sys.exit(app.exec())
