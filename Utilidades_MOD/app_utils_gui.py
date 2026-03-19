import sys
import os
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
                               QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                               QComboBox, QGroupBox, QGridLayout, QFormLayout, QTabWidget,
                               QTextBrowser, QTableWidget, QTableWidgetItem, QHeaderView,
                               QListWidget, QAbstractItemView, QListWidgetItem, QScrollArea,
                               QPlainTextEdit, QSplitter, QMessageBox)
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QUrl, QTimer

# Importar matplotlib para gráficos de Section Designer
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gui_components import StyledButton, LogWidget
from themes import COLORS

# Importar backend
try:
    from .utils_backend import SapUtils, SteelSectionCalc, SlendernessClassifier, SECTION_TYPES, STEEL_MATERIALS
except ImportError:
    try:
        from utils_backend import SapUtils, SteelSectionCalc, SlendernessClassifier, SECTION_TYPES, STEEL_MATERIALS
    except ImportError:
        # Fallback si se ejecuta desde otro directorio
        sys.path.append(os.path.dirname(__file__))
        from utils_backend import SapUtils, SteelSectionCalc, SlendernessClassifier, SECTION_TYPES, STEEL_MATERIALS


def parse_pasted_data(text):
    """
    Parsea datos tabulados pegados por el usuario (CSV/TSV).
    
    Args:
        text: String con datos tabulados (separados por tab o coma)
    
    Returns:
        dict con:
            - 'headers': list de nombres de columnas
            - 'data': dict {column_name: [values_as_float]}
            - 'error': str con mensaje de error si falla el parsing
    """
    try:
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if len(lines) < 2:
            return {'error': 'Se requieren al menos 2 líneas (encabezados + datos)'}
        
        # Detectar separador (tab vs coma)
        first_line = lines[0]
        separator = '\t' if '\t' in first_line else ','
        
        # Parsear encabezados
        headers = [h.strip() for h in first_line.split(separator)]
        
        # Parsear datos
        data = {h: [] for h in headers}
        for i, line in enumerate(lines[1:], start=2):
            values = line.split(separator)
            if len(values) != len(headers):
                return {'error': f'Línea {i}: número de columnas inconsistente (esperadas {len(headers)}, encontradas {len(values)})'}
            
            for header, val in zip(headers, values):
                # Convertir comas decimales a puntos (formato europeo)
                val_clean = val.strip().replace(',', '.')
                try:
                    data[header].append(float(val_clean))
                except ValueError:
                    return {'error': f'Línea {i}, columna "{header}": valor no numérico "{val}"'}
        
        return {'headers': headers, 'data': data, 'error': None}
    
    except Exception as e:
        return {'error': f'Error inesperado al parsear: {str(e)}'}


def parse_interaction_curves(text):
    """
    Parsea el formato especial de múltiples curvas de interacción de SAP2000.
    
    Formato esperado:
    - Línea 1: headers alternando entre "Curve N", "X degrees", empty, ...
    - Línea 2: vacía
    - Líneas siguientes: índice + tríos de valores (P, M2, M3) para cada curva
    
    Returns:
        dict con:
            - 'curves': dict {curve_num: {'name': str, 'angle': str, 'P': [...], 'M2': [...], 'M3': [...]}}
            - 'error': str si hay error
    """
    try:
        lines = [l for l in text.strip().split('\n')]
        if len(lines) < 3:
            return {'error': 'Formato inválido: se requieren al menos 3 líneas'}
        
        # Parsear encabezados de la primera línea
        header_line = lines[0]
        if '\t' not in header_line:
            return {'error': 'Formato inválido: no se detectaron tabs en los encabezados'}
        
        headers = header_line.split('\t')
        
        # Detectar curvas (buscar "Curve N" en los encabezados)
        curves_info = []
        i = 0
        while i < len(headers):
            if 'Curve' in headers[i]:
                curve_num = int(headers[i].replace('Curve', '').strip())
                angle = headers[i+1] if i+1 < len(headers) else ""
                curves_info.append({'num': curve_num, 'angle': angle, 'col_start': i})
                i += 3  # Saltar "Curve N", "X degrees", vacío
            else:
                i += 1
        
        if not curves_info:
            return {'error': 'No se encontraron curvas en el formato esperado'}
        
        # Inicializar estructura de datos para cada curva
        curves = {}
        for curve in curves_info:
            curves[curve['num']] = {
                'name': f"Curve {curve['num']}",
                'angle': curve['angle'],
                'P': [],
                'M2': [],
                'M3': []
            }
        
        # Parsear datos (empezando desde línea 2, índice 1, saltando línea vacía)
        data_start = 2
        for line_idx in range(data_start, len(lines)):
            line = lines[line_idx].strip()
            if not line:
                continue
            
            values = line.split('\t')
            if len(values) < 2:
                continue
            
            # Primer valor es el índice de fila, lo saltamos
            # Luego vienen tríos (P, M2, M3) para cada curva
            val_idx = 1
            for curve_info in curves_info:
                curve_num = curve_info['num']
                if val_idx + 2 < len(values):
                    try:
                        p_val = float(values[val_idx].replace(',', '.'))
                        m2_val = float(values[val_idx + 1].replace(',', '.'))
                        m3_val = float(values[val_idx + 2].replace(',', '.'))
                        
                        curves[curve_num]['P'].append(p_val)
                        curves[curve_num]['M2'].append(m2_val)
                        curves[curve_num]['M3'].append(m3_val)
                        val_idx += 3
                    except (ValueError, IndexError):
                        break
        
        # Validar que al menos una curva tenga datos
        valid_curves = {k: v for k, v in curves.items() if len(v['P']) > 0}
        if not valid_curves:
            return {'error': 'No se pudieron parsear datos numéricos de las curvas'}
        
        return {'curves': valid_curves, 'error': None}
    
    except Exception as e:
        return {'error': f'Error al parsear curvas múltiples: {str(e)}'}


class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setStyleSheet(f"background-color: {COLORS['bg_base']}; border: 1px solid {COLORS['border']};")
        self.mode = None
        self.data = {}

    def update_rect(self, w, l, nx, ny):
        self.mode = "rect"
        self.data = {'w': w, 'l': l, 'nx': nx, 'ny': ny}
        self.update()

    def update_hole(self, os, od, is_, id_, na, nr):
        self.mode = "hole"
        self.data = {'os': os, 'od': od, 'is': is_, 'id': id_, 'na': na, 'nr': nr}
        self.update()

    def draw_dimension(self, painter, p1, p2, text, offset=20):
        """Dibuja una cota minimalista |---| entre p1 y p2 con texto."""
        x1, y1 = p1
        x2, y2 = p2
        
        # Vector dirección
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0: return
        
        # Normal unitaria (dirección del offset)
        # Si vamos de Izq->Der, normal apunta Abajo (Y+)
        nx = -dy / length
        ny = dx / length
        
        # Puntos de la línea de cota
        cx1 = x1 + nx * offset
        cy1 = y1 + ny * offset
        cx2 = x2 + nx * offset
        cy2 = y2 + ny * offset
        
        painter.setPen(QPen(Qt.darkGray, 1))
        
        # Líneas de proyección (del objeto a la cota)
        painter.drawLine(x1, y1, cx1, cy1)
        painter.drawLine(x2, y2, cx2, cy2)
        
        # Línea de cota
        painter.drawLine(cx1, cy1, cx2, cy2)
        
        # Ticks minimalistas (pequeña línea perpendicular a la cota en los extremos)
        tick_size = 4
        # Vector perpendicular a la cota es el vector director original normalizado
        ux = dx / length * tick_size
        uy = dy / length * tick_size
        
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(cx1 - ux, cy1 - uy, cx1 + ux, cy1 + uy) # Tick 1
        painter.drawLine(cx2 - ux, cy2 - uy, cx2 + ux, cy2 + uy) # Tick 2
        
        # Texto
        painter.setPen(QPen(Qt.black, 1))
        
        mid_x = (cx1 + cx2) / 2
        mid_y = (cy1 + cy2) / 2
        
        painter.save()
        painter.translate(mid_x, mid_y)
        
        angle = math.degrees(math.atan2(dy, dx))
        # Ajustar ángulo para lectura cómoda (evitar texto de cabeza)
        if 90 < angle <= 270 or -270 <= angle < -90:
             angle += 180
        
        painter.rotate(angle)
        # Dibujar texto centrado sobre la línea (desplazado un poco en Y local negativo para estar "encima" si rotación es 0)
        # Pero como usamos offset, queremos que esté del lado "afuera".
        # Ajustamos rectángulo de texto
        painter.drawText(-150, -25, 300, 20, Qt.AlignCenter, text)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), Qt.white)
        
        width = self.width()
        height = self.height()
        cx = width / 2
        cy = height / 2
        
        if self.mode == "rect":
            self.draw_rect(painter, cx, cy, width, height)
        elif self.mode == "hole":
            self.draw_hole(painter, cx, cy, width, height)

    def draw_rect(self, painter, cx, cy, w_px, h_px):
        d = self.data
        W_real = d.get('w', 100)
        L_real = d.get('l', 100)
        nx = d.get('nx', 1)
        ny = d.get('ny', 1)
        
        if W_real <= 0 or L_real <= 0: return

        # Scale
        scale = min(w_px / W_real, h_px / L_real) * 0.6 # Reducir escala para dar espacio a cotas
        
        rw = W_real * scale
        rh = L_real * scale
        
        x0 = cx - rw / 2
        y0 = cy - rh / 2 
        
        pen = QPen(Qt.black, 1)
        painter.setPen(pen)
        
        # Draw grid
        # Vertical lines
        if nx > 0:
            for i in range(nx + 1):
                x = x0 + (i * rw / nx)
                painter.drawLine(x, y0, x, y0 + rh)
            
        # Horizontal lines
        if ny > 0:
            for j in range(ny + 1):
                y = y0 + (j * rh / ny)
                painter.drawLine(x0, y, x0 + rw, y)
            
        # Draw border thicker
        painter.setPen(QPen(Qt.blue, 2))
        painter.drawRect(x0, y0, rw, rh)

        # --- Cotas ---
        # Horizontal (Abajo): Izquierda -> Derecha
        dx_val = W_real / nx if nx > 0 else W_real
        text_w = f"{nx} @ {dx_val:.2f} = {W_real:.2f}"
        self.draw_dimension(painter, (x0, y0 + rh), (x0 + rw, y0 + rh), text_w, offset=25)
        
        # Vertical (Izquierda): Arriba -> Abajo (Normal apunta a Izquierda)
        dy_val = L_real / ny if ny > 0 else L_real
        text_h = f"{ny} @ {dy_val:.2f} = {L_real:.2f}"
        self.draw_dimension(painter, (x0, y0), (x0, y0 + rh), text_h, offset=25)

    def draw_hole(self, painter, cx, cy, w_px, h_px):
        d = self.data
        outer_s = d.get('os', 'Cuadrado')
        outer_d = d.get('od', 500)
        inner_s = d.get('is', 'Círculo')
        inner_d = d.get('id', 200)
        na = d.get('na', 16)
        nr = d.get('nr', 2)
        
        if outer_d <= 0: return
        
        scale = (min(w_px, h_px) / outer_d) * 0.6 # Reducir escala para cotas
        
        # Helper to get coords
        def get_coords(shape, dim, n):
            coords = []
            rad = dim / 2.0
            
            # Pre-calc for square
            perimeter = 4.0 * dim
            step = perimeter / float(n) if n > 0 else 0
            
            for i in range(n):
                if shape.lower() == "círculo":
                    ang = 2 * math.pi * i / n
                    u = rad * math.cos(ang)
                    v = rad * math.sin(ang)
                    coords.append((u, v))
                else: # Cuadrado
                    # Equidistant walking along perimeter matching backend logic
                    current_dist = i * step
                    u, v = 0.0, 0.0
                    
                    if current_dist < rad:
                        u, v = rad, current_dist
                    elif current_dist < rad + dim:
                        u, v = rad - (current_dist - rad), rad
                    elif current_dist < rad + 2*dim:
                        u, v = -rad, rad - (current_dist - (rad + dim))
                    elif current_dist < rad + 3*dim:
                        u, v = -rad + (current_dist - (rad + 2*dim)), -rad
                    else:
                        u, v = rad, -rad + (current_dist - (rad + 3*dim))
                        
                    coords.append((u, v))
            return coords

        inner_pts = get_coords(inner_s, inner_d, na)
        outer_pts = get_coords(outer_s, outer_d, na)
        
        pen_mesh = QPen(Qt.gray, 1)
        pen_border = QPen(Qt.blue, 2)
        
        # Draw rings
        for r in range(nr + 1):
            frac = r / float(nr) if nr > 0 else 1.0
            
            # Current ring points
            pts = []
            for i in range(na):
                u_in, v_in = inner_pts[i]
                u_out, v_out = outer_pts[i]
                u = u_in + (u_out - u_in) * frac
                v = v_in + (v_out - v_in) * frac
                # Scale and center (flip Y for screen coords)
                px = cx + u * scale
                py = cy - v * scale 
                pts.append((px, py))
            
            # Draw ring polygon
            painter.setPen(pen_mesh if 0 < r < nr else pen_border)
            for i in range(na):
                p1 = pts[i]
                p2 = pts[(i+1)%na]
                painter.drawLine(p1[0], p1[1], p2[0], p2[1])
                
            # Draw radial lines if not last ring
            if r < nr:
                next_frac = (r + 1) / float(nr)
                painter.setPen(pen_mesh)
                for i in range(na):
                    u_in, v_in = inner_pts[i]
                    u_out, v_out = outer_pts[i]
                    
                    u1 = u_in + (u_out - u_in) * frac
                    v1 = v_in + (v_out - v_in) * frac
                    px1 = cx + u1 * scale
                    py1 = cy - v1 * scale
                    
                    u2 = u_in + (u_out - u_in) * next_frac
                    v2 = v_in + (v_out - v_in) * next_frac
                    px2 = cx + u2 * scale
                    py2 = cy - v2 * scale
                    
                    painter.drawLine(px1, py1, px2, py2)

        # --- Cotas ---
        r_out_px = (outer_d * scale) / 2
        r_in_px = (inner_d * scale) / 2
        
        # Cota Externa (Arriba): Derecha -> Izquierda (Normal apunta Arriba)
        # Usamos el borde superior del bounding box
        self.draw_dimension(painter, 
                            (cx + r_out_px, cy - r_out_px), 
                            (cx - r_out_px, cy - r_out_px), 
                            f"Ext: {outer_d:.2f} ({outer_s})", offset=30)
                            
        # Cota Interna (Abajo): Izquierda -> Derecha (Normal apunta Abajo)
        # Usamos el borde inferior del bounding box interno
        self.draw_dimension(painter, 
                            (cx - r_in_px, cy + r_in_px), 
                            (cx + r_in_px, cy + r_in_px),
                            f"Int: {inner_d:.2f} ({inner_s})", offset=30)

class BaseMeshWidget(QWidget):
    """Clase base para widgets de generación de malla."""
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.backend = None
        self.log_text = None
        self.generate_btn = None
        
        # Iniciar backend con el modelo inyectado si existe
        initial_model = self.sap_interface.SapModel if self.sap_interface else None
        self.backend = SapUtils(sap_model=initial_model)

        # Conectar señal si existe
        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)

    def on_connection_changed(self, connected):
        if connected:
            self.backend.SapModel = self.sap_interface.SapModel
            self.log("📡 Conexión global recibida.")
            if self.generate_btn: self.generate_btn.setEnabled(True)
        else:
            self.backend.SapModel = None
            self.log("📡 Conexión global perdida.")
            if self.generate_btn: self.generate_btn.setEnabled(False)

    def setup_common_ui(self, layout):
        # --- Botones ---
        btn_layout = QHBoxLayout()
        
        self.generate_btn = StyledButton("🔧 Generar Malla", variant="primary")
        self.generate_btn.clicked.connect(self.generate_mesh)

        # Habilitación inicial depende del estado actual, se puede gestionar mejor
        # si sap_interface ya está conectado al inicio
        is_connected = self.sap_interface and self.sap_interface.is_connected()
        self.generate_btn.setEnabled(is_connected if self.sap_interface else False)
        
        btn_layout.addWidget(self.generate_btn)
        layout.addLayout(btn_layout)
        
        # --- Log ---
        grp_log = QGroupBox("Log de Operaciones")
        grp_log_layout = QVBoxLayout()
        self.log_text = LogWidget()
        self.log_text.setFixedHeight(120)
        grp_log_layout.addWidget(self.log_text)
        grp_log.setLayout(grp_log_layout)
        layout.addWidget(grp_log)

    def log(self, message):
        if self.log_text:
            try:
                self.log_text.log(message, level="INFO")
            except Exception:
                try:
                    self.log_text.append(message)
                except Exception:
                    pass

    def ensure_connection(self):
        if not self.backend or not self.backend.SapModel:
            self.log("No hay conexión activa. Intentando reconectar...")
            if self.backend:
                self.backend._connect_to_sap()
            else:
                self.backend = SapUtils()
                
            if not self.backend.SapModel:
                self.log("❌ No se pudo establecer conexión.")
                return False
        return True

    def generate_mesh(self):
        raise NotImplementedError("Debe implementarse en la subclase")


class RectangularMeshWidget(BaseMeshWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent, sap_interface)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Top area: Params + Preview
        top_layout = QHBoxLayout()
        
        # Left side: Parameters
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(0,0,0,0)
        
        # --- Grupo: Parámetros de Malla ---
        grp_params = QGroupBox("Generador de Malla Rectangular")
        form_layout = QFormLayout()
        
        self.width_edit = QLineEdit("500.0")
        self.length_edit = QLineEdit("500.0")
        self.nx_edit = QLineEdit("5")
        self.ny_edit = QLineEdit("5")
        
        form_layout.addRow("Ancho (Dim 1):", self.width_edit)
        form_layout.addRow("Largo (Dim 2):", self.length_edit)
        form_layout.addRow("Divisiones Nx:", self.nx_edit)
        form_layout.addRow("Divisiones Ny:", self.ny_edit)
        
        grp_params.setLayout(form_layout)
        params_layout.addWidget(grp_params)
        
        # --- Grupo: Ubicación y Propiedades ---
        grp_loc = QGroupBox("Ubicación y Propiedades")
        loc_layout = QGridLayout()
        
        self.start_x = QLineEdit("0.0")
        self.start_y = QLineEdit("0.0")
        self.start_z = QLineEdit("0.0")
        
        # Columna Izquierda: Origen
        loc_layout.addWidget(QLabel("Origen X:"), 0, 0)
        loc_layout.addWidget(self.start_x, 0, 1)
        loc_layout.addWidget(QLabel("Origen Y:"), 1, 0)
        loc_layout.addWidget(self.start_y, 1, 1)
        loc_layout.addWidget(QLabel("Origen Z:"), 2, 0)
        loc_layout.addWidget(self.start_z, 2, 1)
        
        # Columna Derecha: Propiedades y Utilidades
        self.prop_edit = QLineEdit("Default")
        self.plane_combo = QComboBox()
        self.plane_combo.addItems(["XY", "XZ", "YZ"])
        self.plane_combo.setCurrentIndex(-1)  # Sin selección inicial
        
        self.btn_get_coords = StyledButton("📍 Obtener Coordenadas", variant="secondary")
        self.btn_get_coords.clicked.connect(self.fetch_coords)
        
        loc_layout.addWidget(QLabel("Propiedad Área:"), 0, 2)
        loc_layout.addWidget(self.prop_edit, 0, 3)
        loc_layout.addWidget(QLabel("Plano:"), 1, 2)
        loc_layout.addWidget(self.plane_combo, 1, 3)
        loc_layout.addWidget(self.btn_get_coords, 2, 2, 1, 2) # Span 2 columns
        
        grp_loc.setLayout(loc_layout)
        params_layout.addWidget(grp_loc)
        
        params_layout.addStretch()
        
        # Right side: Preview
        self.preview = PreviewWidget()
        
        top_layout.addWidget(params_widget, 1)
        top_layout.addWidget(self.preview, 1)
        
        main_layout.addLayout(top_layout)
        
        self.setup_common_ui(main_layout)
        self.setLayout(main_layout)
        
        # Connect signals for preview
        for w in [self.width_edit, self.length_edit, self.nx_edit, self.ny_edit]:
            w.textChanged.connect(self.update_preview)
            
        self.update_preview()

    def update_preview(self):
        try:
            w = float(self.width_edit.text())
            l = float(self.length_edit.text())
            nx = int(self.nx_edit.text())
            ny = int(self.ny_edit.text())
            self.preview.update_rect(w, l, nx, ny)
        except ValueError:
            pass

    def fetch_coords(self):
        if not self.ensure_connection():
            return

        self.log("Obteniendo coordenadas de punto seleccionado...")
        coords = self.backend.get_selected_point_coords()
        
        if coords:
            self.start_x.setText(f"{coords['x']:.4f}")
            self.start_y.setText(f"{coords['y']:.4f}")
            self.start_z.setText(f"{coords['z']:.4f}")
            self.log(f"Coordenadas actualizadas desde punto '{coords['name']}'")
        else:
            self.log("No se encontró ningún punto seleccionado.")

    def generate_mesh(self):
        if not self.ensure_connection():
            return
            
        try:
            w = float(self.width_edit.text())
            l = float(self.length_edit.text())
            nx = int(self.nx_edit.text())
            ny = int(self.ny_edit.text())
            sx = float(self.start_x.text())
            sy = float(self.start_y.text())
            sz = float(self.start_z.text())
            plane = self.plane_combo.currentText()
            prop = self.prop_edit.text()

            from gui_components import InputValidator, show_validation_errors

            errors = []
            ok, msg = InputValidator.validate_positive(self.width_edit.text(), "Ancho")
            if not ok:
                errors.append(msg)
            ok, msg = InputValidator.validate_positive(self.length_edit.text(), "Largo")
            if not ok:
                errors.append(msg)
            ok, msg = InputValidator.validate_numeric(self.nx_edit.text(), "Divisiones X", min_val=1, max_val=200)
            if not ok:
                errors.append(msg)
            ok, msg = InputValidator.validate_numeric(self.ny_edit.text(), "Divisiones Y", min_val=1, max_val=200)
            if not ok:
                errors.append(msg)

            if errors:
                show_validation_errors(self, errors)
                return

            if self.plane_combo.currentIndex() < 0 or plane.strip() == "":
                self.log("⚠️ Seleccione un plano antes de generar la malla.")
                return
            
            self.log(f"Generando malla {nx}x{ny} en {plane}...")
            areas = self.backend.create_mesh_by_coord(w, l, nx, ny, sx, sy, sz, plane, prop)
            
            if areas:
                self.log(f"✅ Éxito: {len(areas)} áreas creadas.")
                self.plane_combo.setCurrentIndex(-1)  # Limpiar selección tras generar
            else:
                self.log("⚠️ No se crearon áreas (o ocurrió un error silencioso).")
                
        except ValueError as e:
            self.log(f"❌ Error en los datos de entrada: {e}")
        except Exception as e:
            self.log(f"❌ Error inesperado: {e}")


class HoleMeshWidget(BaseMeshWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent, sap_interface)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Top area: Params + Preview
        top_layout = QHBoxLayout()
        
        # Left side: Parameters
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        params_layout.setContentsMargins(0,0,0,0)
        
        # --- Grupo: Geometría ---
        grp_geo = QGroupBox("Geometría de Orificio")
        geo_layout = QGridLayout()
        
        # Externo
        geo_layout.addWidget(QLabel("<b>Borde Externo</b>"), 0, 0, 1, 2)
        self.outer_shape = QComboBox()
        self.outer_shape.addItems(["Cuadrado", "Círculo"])
        self.outer_dim = QLineEdit("500.0")
        geo_layout.addWidget(QLabel("Forma:"), 1, 0)
        geo_layout.addWidget(self.outer_shape, 1, 1)
        geo_layout.addWidget(QLabel("Dimensión (Lado/Diámetro):"), 2, 0)
        geo_layout.addWidget(self.outer_dim, 2, 1)
        
        # Interno
        geo_layout.addWidget(QLabel("<b>Orificio Interno</b>"), 0, 2, 1, 2)
        self.inner_shape = QComboBox()
        self.inner_shape.addItems(["Círculo", "Cuadrado"])
        self.inner_dim = QLineEdit("200.0")
        geo_layout.addWidget(QLabel("Forma:"), 1, 2)
        geo_layout.addWidget(self.inner_shape, 1, 3)
        geo_layout.addWidget(QLabel("Dimensión (Lado/Diámetro):"), 2, 2)
        geo_layout.addWidget(self.inner_dim, 2, 3)
        
        grp_geo.setLayout(geo_layout)
        params_layout.addWidget(grp_geo)
        
        # --- Grupo: Malla ---
        grp_mesh = QGroupBox("Configuración de Malla")
        mesh_layout = QFormLayout()
        
        self.num_angular = QComboBox()
        self.num_angular.addItems(["8", "16", "32"])
        self.num_angular.setCurrentText("16")
        self.num_radial = QLineEdit("2")
        
        mesh_layout.addRow("Divisiones Angulares (Puntos por anillo):", self.num_angular)
        mesh_layout.addRow("Divisiones Radiales (Anillos concéntricos):", self.num_radial)
        
        grp_mesh.setLayout(mesh_layout)
        params_layout.addWidget(grp_mesh)
        
        # --- Grupo: Ubicación ---
        grp_loc = QGroupBox("Ubicación y Propiedades")
        loc_layout = QGridLayout()
        
        self.start_x = QLineEdit("0.0")
        self.start_y = QLineEdit("0.0")
        self.start_z = QLineEdit("0.0")
        
        # Columna Izquierda: Origen
        loc_layout.addWidget(QLabel("Origen X (Esquina):"), 0, 0)
        loc_layout.addWidget(self.start_x, 0, 1)
        loc_layout.addWidget(QLabel("Origen Y (Esquina):"), 1, 0)
        loc_layout.addWidget(self.start_y, 1, 1)
        loc_layout.addWidget(QLabel("Origen Z (Esquina):"), 2, 0)
        loc_layout.addWidget(self.start_z, 2, 1)
        
        # Columna Derecha: Propiedades y Utilidades
        self.prop_edit = QLineEdit("Default")
        self.plane_combo = QComboBox()
        self.plane_combo.addItems(["XY", "XZ", "YZ"])
        self.plane_combo.setCurrentIndex(-1)  # Sin selección inicial
        
        self.btn_get_coords = StyledButton("📍 Obtener Coordenadas", variant="secondary")
        self.btn_get_coords.clicked.connect(self.fetch_coords)
        
        loc_layout.addWidget(QLabel("Propiedad Área:"), 0, 2)
        loc_layout.addWidget(self.prop_edit, 0, 3)
        loc_layout.addWidget(QLabel("Plano:"), 1, 2)
        loc_layout.addWidget(self.plane_combo, 1, 3)
        loc_layout.addWidget(self.btn_get_coords, 2, 2, 1, 2)
        
        grp_loc.setLayout(loc_layout)
        params_layout.addWidget(grp_loc)
        
        params_layout.addStretch()
        
        # Wrap params in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(params_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Right side: Preview
        self.preview = PreviewWidget()
        
        top_layout.addWidget(scroll_area, 3)
        top_layout.addWidget(self.preview, 2)
        
        main_layout.addLayout(top_layout)
        
        self.setup_common_ui(main_layout)
        self.setLayout(main_layout)
        
        # Connect signals
        for w in [self.outer_dim, self.inner_dim, self.num_radial]:
            w.textChanged.connect(self.update_preview)
        for w in [self.outer_shape, self.inner_shape, self.num_angular]:
            w.currentIndexChanged.connect(self.update_preview)
            
        self.update_preview()

    def update_preview(self):
        try:
            outer_s = self.outer_shape.currentText()
            outer_d = float(self.outer_dim.text())
            inner_s = self.inner_shape.currentText()
            inner_d = float(self.inner_dim.text())
            n_ang = int(self.num_angular.currentText())
            n_rad = int(self.num_radial.text())
            
            self.preview.update_hole(outer_s, outer_d, inner_s, inner_d, n_ang, n_rad)
        except ValueError:
            pass

    def fetch_coords(self):
        if not self.ensure_connection():
            return

        self.log("Obteniendo coordenadas de punto seleccionado...")
        coords = self.backend.get_selected_point_coords()
        
        if coords:
            self.start_x.setText(f"{coords['x']:.4f}")
            self.start_y.setText(f"{coords['y']:.4f}")
            self.start_z.setText(f"{coords['z']:.4f}")
            self.log(f"Coordenadas actualizadas desde punto '{coords['name']}'")
        else:
            self.log("No se encontró ningún punto seleccionado.")

    def generate_mesh(self):
        if not self.ensure_connection():
            return
            
        try:
            outer_s = self.outer_shape.currentText()
            outer_d = float(self.outer_dim.text())
            inner_s = self.inner_shape.currentText()
            inner_d = float(self.inner_dim.text())
            
            n_ang = int(self.num_angular.currentText())
            n_rad = int(self.num_radial.text())
            
            sx = float(self.start_x.text())
            sy = float(self.start_y.text())
            sz = float(self.start_z.text())
            plane = self.plane_combo.currentText()
            prop = self.prop_edit.text()

            if self.plane_combo.currentIndex() < 0 or plane.strip() == "":
                self.log("⚠️ Seleccione un plano antes de generar la malla.")
                return
            
            self.log(f"Generando malla con orificio ({inner_s} en {outer_s})...")
            areas = self.backend.create_hole_mesh(
                outer_s, outer_d, inner_s, inner_d,
                n_ang, n_rad, sx, sy, sz, plane, prop
            )
            
            if areas:
                self.log(f"✅ Éxito: {len(areas)} áreas creadas.")
                self.plane_combo.setCurrentIndex(-1)  # Limpiar selección tras generar
            else:
                self.log("⚠️ No se crearon áreas.")
                
        except ValueError as e:
            self.log(f"❌ Error en los datos de entrada: {e}")
        except Exception as e:
            self.log(f"❌ Error inesperado: {e}")


class NotesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_refresh = QPushButton("Recargar Notas")
        self.btn_refresh.clicked.connect(self.load_notes)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Markdown Viewer
        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        layout.addWidget(self.viewer)
        
        self.setLayout(layout)
        
        self.load_notes()
        
    def load_notes(self):
        # Buscar el archivo Notas.md en la carpeta Notas/ relativa al script
        base_dir = os.path.dirname(__file__)
        notes_dir = os.path.join(base_dir, "Notas")
        notes_file = os.path.join(notes_dir, "Notas.md")
        
        if os.path.exists(notes_file):
            try:
                with open(notes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Configurar BaseUrl para que las imágenes relativas funcionen
                # Debe ser una URL de archivo (file://...)
                base_url = QUrl.fromLocalFile(notes_dir + os.sep)
                self.viewer.document().setBaseUrl(base_url)
                
                self.viewer.setMarkdown(content)
            except Exception as e:
                self.viewer.setMarkdown(f"# Error al cargar notas\n\n{str(e)}")
        else:
            self.viewer.setMarkdown(f"# Archivo no encontrado\n\nNo se encontró `{notes_file}`.")


class CheckableListGroup(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        
        self.layout_main = QVBoxLayout(self)
        
        # Botones de selección rápida
        btn_layout = QHBoxLayout()
        self.btn_all = QPushButton("Todos")
        self.btn_none = QPushButton("Ninguno")
        
        # Estilo compacto para botones
        for btn in [self.btn_all, self.btn_none]:
            btn.setMaximumHeight(20)
            
        self.btn_all.clicked.connect(self.select_all)
        self.btn_none.clicked.connect(self.select_none)
        
        btn_layout.addWidget(self.btn_all)
        btn_layout.addWidget(self.btn_none)
        #btn_layout.addStretch() # Opcional: si queremos botones a la izquierda
        
        self.layout_main.addLayout(btn_layout)
        
        # Lista
        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(100)
        self.layout_main.addWidget(self.list_widget)
        
    def add_items(self, items):
        self.list_widget.clear()
        for text in items:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
            
    def add_placeholder(self, text):
        self.list_widget.clear()
        item = QListWidgetItem(text)
        item.setFlags(Qt.NoItemFlags)
        self.list_widget.addItem(item)
        
    def get_checked_items(self):
        checked = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked
        
    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # Solo si es seleccionable
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
                
    def select_none(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)

    def clear(self):
        self.list_widget.clear()


class ResultsTableWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        # Instanciar el backend. Si el sap_interface ya tiene modelo, lo pasamos.
        # En cualquier momento que se intente usar, nos aseguraremos de que tenga el modelo actualizado.
        model = self.sap_interface.SapModel if self.sap_interface else None
        self.utils_backend = SapUtils(sap_model=model)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Controles Superiores: Tabla y Acciones ---
        controls_layout = QHBoxLayout()
        
        self.combo_tables = QComboBox()
        self.combo_tables.setMinimumWidth(300)
        self.combo_tables.setPlaceholderText("Seleccione una tabla...")
        
        self.btn_refresh = StyledButton("🔄 Actualizar Lista", variant="secondary")
        self.btn_refresh.setToolTip("Recargar tablas y listas de carga desde SAP2000")
        self.btn_refresh.clicked.connect(self.load_available_data)

        self.btn_load = StyledButton("📥 Cargar Tabla", variant="primary")
        self.btn_load.clicked.connect(self.load_table_data)
        
        controls_layout.addWidget(QLabel("Tabla:"))
        controls_layout.addWidget(self.combo_tables)
        controls_layout.addWidget(self.btn_refresh)
        controls_layout.addWidget(self.btn_load)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # --- Sección de Filtros: Casos y Combinaciones ---
        filters_layout = QHBoxLayout()
        
        # Grupo Casos de Carga
        self.grp_cases = CheckableListGroup("Casos de Carga")
        filters_layout.addWidget(self.grp_cases)
        
        # Grupo Combinaciones
        self.grp_combos = CheckableListGroup("Combinaciones")
        filters_layout.addWidget(self.grp_combos)
        
        layout.addLayout(filters_layout)

        # --- Tabla de Resultados ---
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        
        # Carga inicial si hay conexión
        if self.sap_interface and self.sap_interface.is_connected():
             self.load_available_data()
             
    def load_available_data(self):
        """Carga tablas, casos y combinaciones disponibles."""
        self.combo_tables.clear()
        self.grp_cases.clear()
        self.grp_combos.clear()
        
        # Actualizar referencia del modelo en el backend
        model = self.sap_interface.SapModel if self.sap_interface else None
        self.utils_backend.SapModel = model
        
        if not model:
            self.combo_tables.addItem("Desconectado de SAP2000")
            return

        # 1. Cargar Tablas
        tables = self.utils_backend.get_available_tables()
        if tables:
            tables.sort(key=lambda x: x[1])
            for key, name in tables:
                self.combo_tables.addItem(name, userData=key) 
        else:
            self.combo_tables.addItem("No se encontraron tablas disponibles")

        # 2. Cargar Casos de Carga
        cases = self.utils_backend.get_load_cases()
        if cases:
            self.grp_cases.add_items(cases)
        else:
            self.grp_cases.add_placeholder("(No hay casos)")

        # 3. Cargar Combinaciones
        combos = self.utils_backend.get_load_combos()
        if combos:
            self.grp_combos.add_items(combos)
        else:
            self.grp_combos.add_placeholder("(No hay combos)")

    def load_table_data(self):
        # Verificar selección de tabla
        if self.combo_tables.currentIndex() < 0: return
        table_key = self.combo_tables.currentData()
        if not table_key: return
        
        # Obtener selecciones de Cargas/Combos
        selected_cases = self.grp_cases.get_checked_items()
        selected_combos = self.grp_combos.get_checked_items()
        
        # Validación simple
        if not selected_cases and not selected_combos:
             pass

        # Actualizar referencia del modelo
        model = self.sap_interface.SapModel if self.sap_interface else None
        self.utils_backend.SapModel = model
        
        # UI Feedback
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Cargando...")
        QApplication.processEvents() 
        
        try:
            # Enviamos las listas directamente. Si están vacías (pero no None), el backend se encarga de 
            # enviar el comando de limpieza a SAP2000 (Set... with empty string).
            fields, rows = self.utils_backend.get_table_data(
                table_key, 
                load_cases=selected_cases,
                load_combos=selected_combos
            )
            
            if fields:
                self.setup_table(fields, rows)
            else:
                self.table_widget.setColumnCount(1)
                self.table_widget.setRowCount(1)
                self.table_widget.setHorizontalHeaderLabels(["Mensaje"])
                self.table_widget.setItem(0, 0, QTableWidgetItem("No se pudieron cargar datos (Vacío o Error). Verifica la selección de Cargas/Combos."))
        finally:
            self.btn_load.setEnabled(True)
            self.btn_load.setText("📥 Cargar Tabla")

    def setup_table(self, headers, data):
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setRowCount(len(data))
        
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # Deshabilitar actualizaciones durante la carga masiva para rendimiento
        self.table_widget.setUpdatesEnabled(False)
        try:
            for r, row in enumerate(data):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    # Hacer celdas de solo lectura
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable) 
                    self.table_widget.setItem(r, c, item)
        finally:
            self.table_widget.setUpdatesEnabled(True)
            
        self.table_widget.resizeColumnsToContents()


class SectionPreviewWidget(QWidget):
    """Widget de previsualización de sección transversal de acero."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setStyleSheet(f"background-color: {COLORS['bg_base']}; border: 1px solid {COLORS['border']};")
        self.section_type = None
        self.dims = {}

    def update_section(self, section_type, dims):
        self.section_type = section_type
        self.dims = dict(dims or {})
        self.update()

    def _draw_rect(self, painter, x, y, w, h):
        painter.drawRect(int(round(x)), int(round(y)), int(round(w)), int(round(h)))

    def _draw_dim(self, painter, p1, p2, text, offset=20):
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length <= 1e-9:
            return

        nx = -dy / length
        ny = dx / length

        cx1 = x1 + nx * offset
        cy1 = y1 + ny * offset
        cx2 = x2 + nx * offset
        cy2 = y2 + ny * offset

        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.drawLine(int(x1), int(y1), int(cx1), int(cy1))
        painter.drawLine(int(x2), int(y2), int(cx2), int(cy2))
        painter.drawLine(int(cx1), int(cy1), int(cx2), int(cy2))

        tick = 4
        ux = dx / length * tick
        uy = dy / length * tick
        painter.drawLine(int(cx1 - ux), int(cy1 - uy), int(cx1 + ux), int(cy1 + uy))
        painter.drawLine(int(cx2 - ux), int(cy2 - uy), int(cx2 + ux), int(cy2 + uy))

        painter.drawText(
            int((cx1 + cx2) * 0.5 - 60),
            int((cy1 + cy2) * 0.5 - 12),
            120,
            24,
            Qt.AlignCenter,
            text,
        )

    def _max_dim(self):
        d = self.dims
        t = self.section_type
        if t == "W":
            return max(d.get("d", 0), d.get("bf", 0), d.get("bf_bot", 0) or d.get("bf", 0))
        if t == "C":
            return max(d.get("d", 0), d.get("bf", 0))
        if t == "L":
            return max(d.get("d", 0), d.get("b", 0))
        if t == "HSS_RECT":
            return max(d.get("H", 0), d.get("B", 0))
        if t == "HSS_ROUND":
            return d.get("OD", 0)
        if t == "2L":
            return max(d.get("d", 0), 2 * d.get("b", 0) + d.get("sep", 0))
        if t == "2C":
            return max(d.get("d", 0), 2 * d.get("bf", 0) + d.get("sep", 0))
        if t == "WT":
            return max(d.get("d", 0), d.get("bf", 0))
        return 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(COLORS["bg_base"]))

        if not self.section_type or not self.dims:
            painter.setPen(QPen(QColor(COLORS["text_secondary"]), 1))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin previsualización")
            return

        max_dim = self._max_dim()
        if max_dim <= 0:
            return

        scale = min(self.width(), self.height()) * 0.6 / max_dim
        cx = self.width() * 0.5
        cy = self.height() * 0.5

        painter.setPen(QPen(QColor(COLORS["primary"]), 2))
        painter.setBrush(QBrush(QColor(200, 220, 240)))
        painter.setFont(QFont("Segoe UI", 8))

        draw_map = {
            "W": self._draw_w,
            "C": self._draw_channel,
            "L": self._draw_angle,
            "HSS_RECT": self._draw_hss_rect,
            "HSS_ROUND": self._draw_hss_round,
            "2L": self._draw_double_angle,
            "2C": self._draw_double_channel,
            "WT": self._draw_tee,
        }
        draw_fn = draw_map.get(self.section_type)
        if draw_fn:
            draw_fn(painter, cx, cy, scale, self.dims)

    def _draw_w(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        bf = dims.get("bf", 0)
        tf = dims.get("tf", 0)
        tw = dims.get("tw", 0)
        bf_bot = dims.get("bf_bot", 0) or bf
        tfb = dims.get("tfb", 0) or tf
        if min(d, bf, tf, tw, bf_bot, tfb) <= 0:
            return

        top = cy - d * scale / 2.0
        bot = cy + d * scale / 2.0
        self._draw_rect(painter, cx - bf * scale / 2.0, top, bf * scale, tf * scale)
        self._draw_rect(painter, cx - tw * scale / 2.0, top + tf * scale, tw * scale, (d - tf - tfb) * scale)
        self._draw_rect(painter, cx - bf_bot * scale / 2.0, bot - tfb * scale, bf_bot * scale, tfb * scale)

        self._draw_dim(painter, (cx + bf * scale / 2.0, top), (cx + bf * scale / 2.0, bot), f"d={d:g}", 20)
        self._draw_dim(painter, (cx - bf * scale / 2.0, top), (cx + bf * scale / 2.0, top), f"bf={bf:g}", -24)
        self._draw_dim(painter, (cx - bf * scale / 2.0, top), (cx - bf * scale / 2.0, top + tf * scale), f"tf={tf:g}", -20)
        self._draw_dim(painter, (cx - tw * scale / 2.0, cy), (cx + tw * scale / 2.0, cy), f"tw={tw:g}", 20)
        if abs(bf_bot - bf) > 1e-9:
            self._draw_dim(painter, (cx - bf_bot * scale / 2.0, bot), (cx + bf_bot * scale / 2.0, bot), f"bf_bot={bf_bot:g}", 24)

    def _draw_channel(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        bf = dims.get("bf", 0)
        tf = dims.get("tf", 0)
        tw = dims.get("tw", 0)
        if min(d, bf, tf, tw) <= 0:
            return

        left = cx - bf * scale / 2.0
        top = cy - d * scale / 2.0
        bot = cy + d * scale / 2.0
        self._draw_rect(painter, left, top, tw * scale, d * scale)
        self._draw_rect(painter, left, top, bf * scale, tf * scale)
        self._draw_rect(painter, left, bot - tf * scale, bf * scale, tf * scale)

        self._draw_dim(painter, (left + bf * scale, top), (left + bf * scale, bot), f"d={d:g}", 20)
        self._draw_dim(painter, (left, top), (left + bf * scale, top), f"bf={bf:g}", -24)
        self._draw_dim(painter, (left + bf * scale, top), (left + bf * scale, top + tf * scale), f"tf={tf:g}", 18)
        self._draw_dim(painter, (left, cy), (left + tw * scale, cy), f"tw={tw:g}", 20)

    def _draw_angle(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        b = dims.get("b", 0)
        t = dims.get("t", 0)
        if min(d, b, t) <= 0:
            return

        left = cx - b * scale / 2.0
        top = cy - d * scale / 2.0
        bot = cy + d * scale / 2.0
        self._draw_rect(painter, left, top, t * scale, d * scale)
        self._draw_rect(painter, left, bot - t * scale, b * scale, t * scale)

        self._draw_dim(painter, (left + b * scale, top), (left + b * scale, bot), f"d={d:g}", 20)
        self._draw_dim(painter, (left, bot), (left + b * scale, bot), f"b={b:g}", 24)
        self._draw_dim(painter, (left, top), (left + t * scale, top), f"t={t:g}", -22)

    def _draw_hss_rect(self, painter, cx, cy, scale, dims):
        h = dims.get("H", 0)
        b = dims.get("B", 0)
        t = dims.get("t", 0)
        if min(h, b, t) <= 0 or h <= 2 * t or b <= 2 * t:
            return

        x0 = cx - b * scale / 2.0
        y0 = cy - h * scale / 2.0
        self._draw_rect(painter, x0, y0, b * scale, h * scale)

        painter.setBrush(QBrush(Qt.white))
        self._draw_rect(
            painter,
            x0 + t * scale,
            y0 + t * scale,
            (b - 2 * t) * scale,
            (h - 2 * t) * scale,
        )
        painter.setBrush(QBrush(QColor(200, 220, 240)))

        self._draw_dim(painter, (x0 + b * scale, y0), (x0 + b * scale, y0 + h * scale), f"H={h:g}", 20)
        self._draw_dim(painter, (x0, y0), (x0 + b * scale, y0), f"B={b:g}", -24)
        self._draw_dim(painter, (x0, y0), (x0 + t * scale, y0), f"t={t:g}", -20)

    def _draw_hss_round(self, painter, cx, cy, scale, dims):
        od = dims.get("OD", 0)
        t = dims.get("t", 0)
        if min(od, t) <= 0 or od <= 2 * t:
            return

        r_out = od * scale / 2.0
        r_in = (od - 2 * t) * scale / 2.0
        painter.drawEllipse(int(cx - r_out), int(cy - r_out), int(2 * r_out), int(2 * r_out))

        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(int(cx - r_in), int(cy - r_in), int(2 * r_in), int(2 * r_in))
        painter.setBrush(QBrush(QColor(200, 220, 240)))

        self._draw_dim(painter, (cx - r_out, cy), (cx + r_out, cy), f"OD={od:g}", 24)
        self._draw_dim(painter, (cx + r_in, cy), (cx + r_out, cy), f"t={t:g}", -20)

    def _draw_double_angle(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        b = dims.get("b", 0)
        t = dims.get("t", 0)
        sep = dims.get("sep", 0)
        if min(d, b, t) <= 0 or sep < 0:
            return

        top = cy - d * scale / 2.0
        bot = cy + d * scale / 2.0
        gap = sep * scale

        xr = cx + gap / 2.0
        self._draw_rect(painter, xr, top, t * scale, d * scale)
        self._draw_rect(painter, xr, bot - t * scale, b * scale, t * scale)

        xl = cx - gap / 2.0
        self._draw_rect(painter, xl - t * scale, top, t * scale, d * scale)
        self._draw_rect(painter, xl - b * scale, bot - t * scale, b * scale, t * scale)

        self._draw_dim(painter, (xr + b * scale, top), (xr + b * scale, bot), f"d={d:g}", 18)
        self._draw_dim(painter, (xr, bot), (xr + b * scale, bot), f"b={b:g}", 22)
        self._draw_dim(painter, (xr, top), (xr + t * scale, top), f"t={t:g}", -20)
        self._draw_dim(painter, (xl, cy), (xr, cy), f"sep={sep:g}", 20)

    def _draw_double_channel(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        bf = dims.get("bf", 0)
        tf = dims.get("tf", 0)
        tw = dims.get("tw", 0)
        sep = dims.get("sep", 0)
        if min(d, bf, tf, tw) <= 0 or sep < 0:
            return

        top = cy - d * scale / 2.0
        bot = cy + d * scale / 2.0
        gap = sep * scale

        xl = cx - gap / 2.0
        self._draw_rect(painter, xl - tw * scale, top, tw * scale, d * scale)
        self._draw_rect(painter, xl - bf * scale, top, bf * scale, tf * scale)
        self._draw_rect(painter, xl - bf * scale, bot - tf * scale, bf * scale, tf * scale)

        xr = cx + gap / 2.0
        self._draw_rect(painter, xr, top, tw * scale, d * scale)
        self._draw_rect(painter, xr, top, bf * scale, tf * scale)
        self._draw_rect(painter, xr, bot - tf * scale, bf * scale, tf * scale)

        self._draw_dim(painter, (xr + bf * scale, top), (xr + bf * scale, bot), f"d={d:g}", 18)
        self._draw_dim(painter, (xr, top), (xr + bf * scale, top), f"bf={bf:g}", -22)
        self._draw_dim(painter, (xr + bf * scale, top), (xr + bf * scale, top + tf * scale), f"tf={tf:g}", 18)
        self._draw_dim(painter, (xr, cy), (xr + tw * scale, cy), f"tw={tw:g}", 20)
        self._draw_dim(painter, (xl, cy), (xr, cy), f"sep={sep:g}", 24)

    def _draw_tee(self, painter, cx, cy, scale, dims):
        d = dims.get("d", 0)
        bf = dims.get("bf", 0)
        tf = dims.get("tf", 0)
        tw = dims.get("tw", 0)
        if min(d, bf, tf, tw) <= 0 or d <= tf:
            return

        top = cy - d * scale / 2.0
        stem_h = d - tf
        self._draw_rect(painter, cx - bf * scale / 2.0, top, bf * scale, tf * scale)
        self._draw_rect(painter, cx - tw * scale / 2.0, top + tf * scale, tw * scale, stem_h * scale)

        self._draw_dim(painter, (cx + bf * scale / 2.0, top), (cx + bf * scale / 2.0, top + d * scale), f"d={d:g}", 20)
        self._draw_dim(painter, (cx - bf * scale / 2.0, top), (cx + bf * scale / 2.0, top), f"bf={bf:g}", -24)
        self._draw_dim(painter, (cx + bf * scale / 2.0, top), (cx + bf * scale / 2.0, top + tf * scale), f"tf={tf:g}", 18)
        self._draw_dim(painter, (cx - tw * scale / 2.0, cy), (cx + tw * scale / 2.0, cy), f"tw={tw:g}", 20)


class FrameSectionWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.backend = None
        self._recalc_timer = None
        self.dim_edits = {}
        self.prop_value_labels = {}
        self.last_props = None
        self.last_slenderness = None

        initial_model = self.sap_interface.SapModel if self.sap_interface else None
        self.backend = SapUtils(sap_model=initial_model)

        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)

        self.init_ui()
        self._recalculate()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        type_group = QGroupBox("Tipo de Sección")
        type_layout = QVBoxLayout(type_group)
        self.type_combo = QComboBox()
        for key, cfg in SECTION_TYPES.items():
            self.type_combo.addItem(cfg.get("display", key), userData=key)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        left_layout.addWidget(type_group)

        dims_group = QGroupBox("Dimensiones (unidades del modelo)")
        self.dims_form = QFormLayout(dims_group)
        left_layout.addWidget(dims_group)

        material_group = QGroupBox("Material")
        material_layout = QVBoxLayout(material_group)
        self.material_source_combo = QComboBox()
        self.material_source_combo.addItems(["Predefinido", "Del Modelo SAP2000"])
        self.material_source_combo.currentTextChanged.connect(self._on_material_source_changed)
        material_layout.addWidget(self.material_source_combo)

        self.material_combo = QComboBox()
        self.material_combo.currentTextChanged.connect(self._on_material_changed)
        material_layout.addWidget(self.material_combo)

        mat_form = QFormLayout()
        self.fy_edit = QLineEdit("345")
        self.e_edit = QLineEdit("200000")
        self.fu_edit = QLineEdit("450")
        self.fy_edit.textChanged.connect(self._schedule_recalc)
        self.e_edit.textChanged.connect(self._schedule_recalc)
        self.fu_edit.textChanged.connect(self._schedule_recalc)
        mat_form.addRow("Fy (MPa):", self.fy_edit)
        mat_form.addRow("E (MPa):", self.e_edit)
        mat_form.addRow("Fu (MPa):", self.fu_edit)
        material_layout.addLayout(mat_form)
        left_layout.addWidget(material_group)

        name_group = QGroupBox("Nombre de Sección")
        name_layout = QVBoxLayout(name_group)
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        left_layout.addWidget(name_group)

        left_scroll_content = QWidget()
        left_scroll_content.setLayout(left_layout)
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_scroll_content)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QScrollArea.NoFrame)

        self.preview_widget = SectionPreviewWidget()

        # --- Properties as vertical list (middle column) ---
        props_group = QGroupBox("Propiedades de la Sección")
        props_inner_layout = QVBoxLayout()
        props_inner_layout.setSpacing(2)
        value_font = QFont("Consolas", 10)
        value_font.setStyleHint(QFont.Monospace)

        keys = ["A", "Ix", "Iy", "rx", "ry", "J", "Sx_top", "Sx_bot", "Sy", "Zx", "Zy", "Cw"]
        labels = {
            "A": "A", "Ix": "Ix", "Iy": "Iy", "rx": "rx", "ry": "ry", "J": "J",
            "Sx_top": "Sx_top", "Sx_bot": "Sx_bot", "Sy": "Sy",
            "Zx": "Zx", "Zy": "Zy", "Cw": "Cw",
        }
        for key in keys:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(4)
            name_label = QLabel(f"{labels[key]}:")
            name_label.setFixedWidth(55)
            val_lbl = QLabel("--")
            val_lbl.setFont(value_font)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(name_label)
            row_layout.addWidget(val_lbl)
            props_inner_layout.addLayout(row_layout)
            self.prop_value_labels[key] = val_lbl
        props_inner_layout.addStretch(1)

        props_scroll_content = QWidget()
        props_scroll_content.setLayout(props_inner_layout)
        props_scroll = QScrollArea()
        props_scroll.setWidget(props_scroll_content)
        props_scroll.setWidgetResizable(True)
        props_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        props_group_layout = QVBoxLayout(props_group)
        props_group_layout.setContentsMargins(4, 4, 4, 4)
        props_group_layout.addWidget(props_scroll)

        # --- Three-column top layout ---
        top_layout.addWidget(left_scroll, 2)
        top_layout.addWidget(props_group, 1)
        top_layout.addWidget(self.preview_widget, 2)
        main_layout.addLayout(top_layout)

        slender_group = QGroupBox("Clasificación de Esbeltez - AISC 360-16")
        slender_layout = QVBoxLayout(slender_group)
        self.slenderness_table = QTableWidget(0, 8)
        self.slenderness_table.setHorizontalHeaderLabels([
            "Elemento",
            "λ",
            "Fórmula",
            "λp",
            "λr (Flexión)",
            "Clasif. Flexión",
            "λr (Compresión)",
            "Clasif. Compresión",
        ])
        self.slenderness_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.slenderness_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        slender_layout.addWidget(self.slenderness_table)

        self.overall_label = QLabel("Clasificación Global - Flexión: -- | Compresión: --")
        self.overall_label.setStyleSheet(
            f"padding: 6px; border: 1px solid {COLORS['border']};"
            f"background-color: {COLORS['bg_base']}; color: {COLORS['text_primary']}; font-weight: bold;"
        )
        slender_layout.addWidget(self.overall_label)
        main_layout.addWidget(slender_group)

        actions_layout = QHBoxLayout()
        self.import_btn = StyledButton("📤 Importar a SAP2000", variant="success")
        self.copy_btn = StyledButton("📋 Copiar Resultados", variant="secondary")
        self.import_btn.clicked.connect(self._on_import)
        self.copy_btn.clicked.connect(self._on_copy)
        actions_layout.addWidget(self.import_btn)
        actions_layout.addWidget(self.copy_btn)
        main_layout.addLayout(actions_layout)

        self.log_widget = LogWidget()
        self.log_widget.setFixedHeight(100)
        main_layout.addWidget(self.log_widget)

        self._on_material_source_changed(self.material_source_combo.currentText())
        self._on_type_changed()
        self.on_connection_changed(bool(self.backend.SapModel))

    def _clear_form_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_type_changed(self):
        self._clear_form_layout(self.dims_form)
        self.dim_edits = {}

        section_type = self.type_combo.currentData()
        section_cfg = SECTION_TYPES.get(section_type, {})
        for key, label, default in section_cfg.get("params", []):
            edit = QLineEdit(str(default))
            edit.textChanged.connect(self._on_dims_changed)
            self.dims_form.addRow(f"{label}:", edit)
            self.dim_edits[key] = edit

        self._auto_name()
        self._recalculate()

    def _on_dims_changed(self):
        self._auto_name()
        self._schedule_recalc()

    def _schedule_recalc(self):
        if self._recalc_timer is not None:
            self._recalc_timer.stop()
        self._recalc_timer = QTimer()
        self._recalc_timer.setSingleShot(True)
        self._recalc_timer.timeout.connect(self._recalculate)
        self._recalc_timer.start(300)

    def _read_dims(self):
        dims = {}
        for key, edit in self.dim_edits.items():
            txt = edit.text().strip().replace(",", ".")
            if txt == "":
                return None
            dims[key] = float(txt)
        return dims

    def _auto_name(self):
        section_type = self.type_combo.currentData()
        dims = {}
        for key, edit in self.dim_edits.items():
            try:
                dims[key] = float(edit.text().strip().replace(",", "."))
            except ValueError:
                return

        if section_type == "W":
            name = f"W{dims.get('d', 0):g}x{dims.get('bf', 0):g}"
        elif section_type == "C":
            name = f"C{dims.get('d', 0):g}x{dims.get('bf', 0):g}"
        elif section_type == "L":
            name = f"L{dims.get('d', 0):g}x{dims.get('b', 0):g}x{dims.get('t', 0):g}"
        elif section_type == "HSS_RECT":
            name = f"HSS{dims.get('H', 0):g}x{dims.get('B', 0):g}x{dims.get('t', 0):g}"
        elif section_type == "HSS_ROUND":
            name = f"HSS_R{dims.get('OD', 0):g}x{dims.get('t', 0):g}"
        elif section_type == "2L":
            name = f"2L{dims.get('d', 0):g}x{dims.get('b', 0):g}x{dims.get('t', 0):g}"
        elif section_type == "2C":
            name = f"2C{dims.get('d', 0):g}x{dims.get('bf', 0):g}"
        elif section_type == "WT":
            name = f"WT{dims.get('d', 0):g}x{dims.get('bf', 0):g}"
        else:
            name = ""

        self.name_edit.setText(name)

    def _on_material_source_changed(self, source):
        self.material_combo.blockSignals(True)
        self.material_combo.clear()

        if source == "Predefinido":
            mats = list(STEEL_MATERIALS.keys()) + ["Personalizado"]
            self.material_combo.addItems(mats)
            self.material_combo.setEnabled(True)
            self.material_combo.setCurrentIndex(0)
        else:
            mats = self.backend.get_steel_materials()
            if mats:
                self.material_combo.addItems(mats)
                self.material_combo.setEnabled(True)
            else:
                self.material_combo.addItem("Sin materiales")
                self.material_combo.setEnabled(False)
                self.log_widget.log("No se encontraron materiales de acero en SAP2000.", "WARNING")

        self.material_combo.blockSignals(False)
        self._on_material_changed(self.material_combo.currentText())

    def _on_material_changed(self, material_name):
        if self.material_source_combo.currentText() == "Predefinido":
            if material_name in STEEL_MATERIALS:
                data = STEEL_MATERIALS[material_name]
                self.fy_edit.setText(f"{float(data.get('Fy_MPa', 0)):g}")
                self.e_edit.setText(f"{float(data.get('E_MPa', 0)):g}")
                self.fu_edit.setText(f"{float(data.get('Fu_MPa', 0)):g}")
            elif material_name == "Personalizado":
                self.fy_edit.clear()
                self.e_edit.clear()
                self.fu_edit.clear()
        self._schedule_recalc()

    def _fmt(self, value):
        if value is None:
            return "--"
        try:
            abs_v = abs(float(value))
            if abs_v >= 1000:
                return f"{value:,.2f}"
            if abs_v >= 1:
                return f"{value:,.3f}"
            return f"{value:,.4f}"
        except Exception:
            return "--"

    def _clear_outputs(self):
        for lbl in self.prop_value_labels.values():
            lbl.setText("--")
        self.slenderness_table.setRowCount(0)
        self.overall_label.setText("Clasificación Global - Flexión: -- | Compresión: --")
        self.overall_label.setStyleSheet(
            f"padding: 6px; border: 1px solid {COLORS['border']};"
            f"background-color: {COLORS['bg_base']}; color: {COLORS['text_primary']}; font-weight: bold;"
        )
        self.last_props = None
        self.last_slenderness = None

    def _update_properties(self, props):
        if not props:
            for lbl in self.prop_value_labels.values():
                lbl.setText("--")
            return
        for key, lbl in self.prop_value_labels.items():
            lbl.setText(self._fmt(props.get(key)))

    def _classification_style(self, text):
        if text in ("Compacto", "No Esbelto"):
            return QColor("#c8e6c9"), QColor("#2e7d32")
        if text == "No Compacto":
            return QColor("#fff9c4"), QColor("#f57f17")
        return QColor("#ffcdd2"), QColor("#c62828")

    def _set_read_only(self, item):
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)

    def _update_slenderness(self, data):
        self.slenderness_table.setRowCount(0)
        if not data:
            self.overall_label.setText("Clasificación Global - Flexión: -- | Compresión: --")
            return

        elements = data.get("elements", [])
        self.slenderness_table.setRowCount(len(elements))
        for row, elem in enumerate(elements):
            values = [
                elem.get("name", ""),
                self._fmt(elem.get("lambda_val")),
                elem.get("formula", ""),
                self._fmt(elem.get("lambda_p")),
                self._fmt(elem.get("lambda_r_flex")),
                elem.get("class_flexure", ""),
                self._fmt(elem.get("lambda_r_comp")),
                elem.get("class_compression", ""),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                self._set_read_only(item)
                if col in (5, 7):
                    bg, fg = self._classification_style(str(val))
                    item.setBackground(bg)
                    item.setForeground(fg)
                self.slenderness_table.setItem(row, col, item)

        overall_flex = data.get("overall_flexure", "--")
        overall_comp = data.get("overall_compression", "--")
        self.overall_label.setText(
            f"Clasificación Global - Flexión: {overall_flex} | Compresión: {overall_comp}"
        )

        worst = "OK"
        if "Esbelto" in (overall_flex, overall_comp):
            worst = "ERROR"
        elif overall_flex == "No Compacto":
            worst = "WARNING"

        if worst == "ERROR":
            bg = "#ffcdd2"
            fg = "#c62828"
        elif worst == "WARNING":
            bg = "#fff9c4"
            fg = "#f57f17"
        else:
            bg = "#c8e6c9"
            fg = "#2e7d32"
        self.overall_label.setStyleSheet(
            f"padding: 6px; border: 1px solid {COLORS['border']};"
            f"background-color: {bg}; color: {fg}; font-weight: bold;"
        )

    def _recalculate(self):
        section_type = self.type_combo.currentData()
        if not section_type:
            self._clear_outputs()
            return

        try:
            dims = self._read_dims()
            if not dims:
                self._clear_outputs()
                self.preview_widget.update_section(section_type, {})
                return

            props = SteelSectionCalc.calc_properties(section_type, dims)
            self.last_props = props
            self._update_properties(props)

            try:
                fy = float(self.fy_edit.text().strip().replace(",", "."))
                e_val = float(self.e_edit.text().strip().replace(",", "."))
            except ValueError:
                fy = None
                e_val = None

            slenderness = None
            if fy and e_val:
                slenderness = SlendernessClassifier.classify(section_type, dims, fy, e_val)
            self.last_slenderness = slenderness
            self._update_slenderness(slenderness)
            self.preview_widget.update_section(section_type, dims)
        except Exception:
            self._clear_outputs()
            self.preview_widget.update_section(section_type, {})

    def _on_import(self):
        section_name = self.name_edit.text().strip()
        material = self.material_combo.currentText().strip()
        section_type = self.type_combo.currentData()

        if not section_name:
            self.log_widget.log("Ingrese un nombre de sección válido.", "WARNING")
            return
        if not material or material == "Sin materiales":
            self.log_widget.log("Seleccione un material válido.", "WARNING")
            return

        try:
            dims = self._read_dims()
        except Exception:
            dims = None
        if not dims:
            self.log_widget.log("Dimensiones inválidas para importar.", "ERROR")
            return

        if self.material_source_combo.currentText() == "Predefinido":
            self.log_widget.log("Verifique que el nombre de material exista en SAP2000.", "INFO")

        ok = self.backend.create_frame_section(section_type, section_name, material, dims)
        if ok:
            self.log_widget.log(f"Sección '{section_name}' importada correctamente.", "SUCCESS")
        else:
            self.log_widget.log(f"No se pudo importar la sección '{section_name}'.", "ERROR")

    def _on_copy(self):
        lines = []
        lines.append("=== PROPIEDADES DE SECCIÓN ===")
        lines.append(f"Tipo: {self.type_combo.currentText()}")
        lines.append(f"Nombre: {self.name_edit.text().strip()}")
        lines.append(f"Material: {self.material_combo.currentText().strip()}")
        lines.append("")

        if self.last_props:
            for key in ["A", "Ix", "Iy", "Sx_top", "Sx_bot", "Sy", "Zx", "Zy", "rx", "ry", "J", "Cw"]:
                lines.append(f"{key}: {self._fmt(self.last_props.get(key))}")
        else:
            lines.append("Sin resultados de propiedades")

        lines.append("")
        lines.append("=== ESBELTEZ AISC 360-16 ===")
        if self.last_slenderness and self.last_slenderness.get("elements"):
            lines.append("Elemento | λ | Fórmula | λp | λr(F) | Clasif. F | λr(C) | Clasif. C")
            for elem in self.last_slenderness["elements"]:
                lines.append(
                    " | ".join([
                        str(elem.get("name", "")),
                        self._fmt(elem.get("lambda_val")),
                        str(elem.get("formula", "")),
                        self._fmt(elem.get("lambda_p")),
                        self._fmt(elem.get("lambda_r_flex")),
                        str(elem.get("class_flexure", "")),
                        self._fmt(elem.get("lambda_r_comp")),
                        str(elem.get("class_compression", "")),
                    ])
                )
            lines.append("")
            lines.append(
                f"Global - Flexión: {self.last_slenderness.get('overall_flexure', '--')} | "
                f"Compresión: {self.last_slenderness.get('overall_compression', '--')}"
            )
        else:
            lines.append("Sin resultados de esbeltez")

        QApplication.clipboard().setText("\n".join(lines))
        self.log_widget.log("Resultados copiados al portapapeles.", "SUCCESS")

    def on_connection_changed(self, connected):
        if connected:
            self.backend.SapModel = self.sap_interface.SapModel
            self.import_btn.setEnabled(True)
            self.log_widget.log("📡 Conexión establecida", "SUCCESS")
        else:
            self.backend.SapModel = None
            self.import_btn.setEnabled(False)
            self.log_widget.log("📡 Conexión perdida", "WARNING")


class MomentoCurvaturaWidget(QWidget):
    """Widget para graficar curvas Momento-Curvatura de Section Designer."""
    
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.parsed_data = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter horizontal (datos | gráfico)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # --- Panel Izquierdo: Entrada de datos ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Área de texto para pegar datos
        grp_input = QGroupBox("Datos del Section Designer")
        input_layout = QVBoxLayout(grp_input)
        
        lbl_instrucciones = QLabel(
            "📋 Pegar datos tabulados de SAP2000 Section Designer\n"
            "Se requieren columnas 'Curvature' y 'Moment'"
        )
        lbl_instrucciones.setWordWrap(True)
        input_layout.addWidget(lbl_instrucciones)
        
        self.txt_input = QPlainTextEdit()
        self.txt_input.setPlaceholderText(
            "Conc. Strain\tNeutral Axis\tSteel Strain\t...\tCurvature\tMoment\n"
            "0\t0\t0\t...\t0\t0\n"
            "-1,175E-05\t0,1409\t3,585E-05\t...\t1,077E-04\t0,2414"
        )
        self.txt_input.setMinimumHeight(150)
        input_layout.addWidget(self.txt_input)
        
        btn_process = StyledButton("📊 Procesar y Graficar", variant="primary")
        btn_process.clicked.connect(self.process_and_plot)
        input_layout.addWidget(btn_process)
        
        left_layout.addWidget(grp_input)
        
        # Momento Último
        grp_momento_ultimo = QGroupBox("Momento Último")
        momento_layout = QHBoxLayout(grp_momento_ultimo)
        
        lbl_mu = QLabel("Mu:")
        momento_layout.addWidget(lbl_mu)
        
        self.txt_momento_ultimo = QLineEdit()
        self.txt_momento_ultimo.setPlaceholderText("Ej: 20.5")
        self.txt_momento_ultimo.textChanged.connect(self.on_momento_ultimo_changed)
        momento_layout.addWidget(self.txt_momento_ultimo)
        
        left_layout.addWidget(grp_momento_ultimo)
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # --- Panel Derecho: Gráfico ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)
            
            right_layout.addWidget(self.toolbar)
            right_layout.addWidget(self.canvas)
        else:
            lbl_no_mpl = QLabel(
                "⚠️ Matplotlib no instalado.\n\n"
                "Para habilitar gráficos, ejecute:\n"
                "pip install matplotlib"
            )
            lbl_no_mpl.setAlignment(Qt.AlignCenter)
            lbl_no_mpl.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12pt;")
            right_layout.addWidget(lbl_no_mpl)
        
        splitter.addWidget(right_widget)
        
        # Proporciones 40% izquierda, 60% derecha
        splitter.setSizes([400, 600])
    
    def process_and_plot(self):
        """Procesa los datos pegados y genera el gráfico."""
        text = self.txt_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Sin Datos", "Por favor pegue los datos del Section Designer.")
            return
        
        # Parsear datos
        result = parse_pasted_data(text)
        if result.get('error'):
            QMessageBox.critical(self, "Error de Parsing", f"Error al procesar datos:\n\n{result['error']}")
            return
        
        self.parsed_data = result
        headers = result['headers']
        data = result['data']
        
        # Validar columnas requeridas
        if 'Curvature' not in headers or 'Moment' not in headers:
            QMessageBox.critical(
                self, "Columnas Faltantes",
                f"Se requieren las columnas 'Curvature' y 'Moment'.\n\nColumnas encontradas:\n{', '.join(headers)}"
            )
            return
        
        # Graficar
        if MATPLOTLIB_AVAILABLE:
            self.plot_moment_curvature(data)
    
    def on_momento_ultimo_changed(self):
        """Redibuja el gráfico cuando cambia el momento último."""
        if self.parsed_data and MATPLOTLIB_AVAILABLE:
            self.plot_moment_curvature(self.parsed_data['data'])
    
    def plot_moment_curvature(self, data):
        """Genera el gráfico Momento vs Curvatura."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        curvature = data['Curvature']
        moment = data['Moment']
        
        ax.plot(curvature, moment, 'b-', linewidth=2, label='M vs φ')
        
        # Dibujar línea de momento último si está especificado
        momento_ultimo_text = self.txt_momento_ultimo.text().strip()
        if momento_ultimo_text:
            try:
                momento_ultimo = float(momento_ultimo_text.replace(',', '.'))
                ax.axhline(y=momento_ultimo, color='r', linestyle='--', linewidth=2, label=f'Mu = {momento_ultimo}')
            except ValueError:
                pass  # Si no es un número válido, no dibujamos la línea
        
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xlabel('Curvatura φ [1/unit]', fontsize=11)
        ax.set_ylabel('Momento M [unit]', fontsize=11)
        ax.set_title('Curva Momento-Curvatura (Section Designer)', fontsize=12, fontweight='bold')
        ax.legend()
        
        self.figure.tight_layout()
        self.canvas.draw()


class PMWidget(QWidget):
    """Widget para graficar diagramas de interacción P-M2-M3."""
    
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.parsed_data = None
        self.multi_curve_mode = False
        self.curves_data = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Splitter horizontal (datos | gráfico)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # --- Panel Izquierdo: Entrada de datos ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Área de texto para pegar datos
        grp_input = QGroupBox("Datos del Section Designer")
        input_layout = QVBoxLayout(grp_input)
        
        lbl_instrucciones = QLabel(
            "📋 Pegar datos tabulados de SAP2000 Section Designer\n"
            "Se requieren columnas con 'P', 'M2' y/o 'M3'"
        )
        lbl_instrucciones.setWordWrap(True)
        input_layout.addWidget(lbl_instrucciones)
        
        self.txt_input = QPlainTextEdit()
        self.txt_input.setPlaceholderText(
            "Formato simple: P\tM2\tM3\n"
            "O formato múltiples curvas: Curve 1\t0 degrees\t..."
        )
        self.txt_input.setMinimumHeight(150)
        input_layout.addWidget(self.txt_input)
        
        # Selector de tipo de gráfico (P-M2 o P-M3)
        tipo_layout = QHBoxLayout()
        tipo_layout.addWidget(QLabel("Seleccionar Curva a Graficar:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["P-M2", "P-M3"])
        tipo_layout.addWidget(self.combo_tipo)
        tipo_layout.addStretch()
        input_layout.addLayout(tipo_layout)
        
        btn_process = StyledButton("📊 Procesar y Graficar", variant="primary")
        btn_process.clicked.connect(self.process_and_plot)
        input_layout.addWidget(btn_process)
        
        left_layout.addWidget(grp_input)
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # --- Panel Derecho: Gráfico ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 6), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)
            
            right_layout.addWidget(self.toolbar)
            right_layout.addWidget(self.canvas)
        else:
            lbl_no_mpl = QLabel(
                "⚠️ Matplotlib no instalado.\n\n"
                "Para habilitar gráficos, ejecute:\n"
                "pip install matplotlib"
            )
            lbl_no_mpl.setAlignment(Qt.AlignCenter)
            lbl_no_mpl.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12pt;")
            right_layout.addWidget(lbl_no_mpl)
        
        splitter.addWidget(right_widget)
        
        # Proporciones 40% izquierda, 60% derecha
        splitter.setSizes([400, 600])
    
    def process_and_plot(self):
        """Procesa los datos pegados y genera el gráfico."""
        text = self.txt_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Sin Datos", "Por favor pegue los datos del Section Designer.")
            return
        
        tipo = self.combo_tipo.currentText()  # "P-M2" o "P-M3"
        
        # Intentar primero parsear como formato de múltiples curvas
        multi_result = parse_interaction_curves(text)
        
        if not multi_result.get('error'):
            # Es formato de múltiples curvas - seleccionar automáticamente según tipo
            self.multi_curve_mode = True
            self.curves_data = multi_result['curves']
            
            # Seleccionar curvas según tipo
            if tipo == "P-M3":
                target_curves = [1, 13]  # 0° y 180°
            else:  # P-M2
                target_curves = [7, 19]  # 90° y 270°
            
            # Graficar las curvas seleccionadas
            if MATPLOTLIB_AVAILABLE:
                self.plot_multi_curves(tipo, target_curves)
        else:
            # No es formato múltiple, intentar formato simple
            simple_result = parse_pasted_data(text)
            if simple_result.get('error'):
                QMessageBox.critical(self, "Error de Parsing", 
                    f"No se pudo parsear como formato múltiple ni simple:\n\n"
                    f"Múltiples curvas: {multi_result['error']}\n"
                    f"Formato simple: {simple_result['error']}")
                return
            
            self.multi_curve_mode = False
            self.parsed_data = simple_result
            headers = simple_result['headers']
            data = simple_result['data']
            
            # Validar columnas según tipo de gráfico
            required_cols = ['P', 'M2'] if tipo == "P-M2" else ['P', 'M3']
            missing = [c for c in required_cols if c not in headers]
            
            if missing:
                QMessageBox.critical(
                    self, "Columnas Faltantes",
                    f"Para el gráfico '{tipo}' se requieren las columnas: {', '.join(required_cols)}\n\n"
                    f"Columnas faltantes: {', '.join(missing)}\n\n"
                    f"Columnas encontradas: {', '.join(headers)}"
                )
                return
            
            # Graficar formato simple
            if MATPLOTLIB_AVAILABLE:
                self.plot_simple(data, tipo)
    
    def plot_multi_curves(self, tipo, target_curves):
        """Grafica múltiples curvas de interacción en el mismo gráfico."""
        if not self.curves_data:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Colores para las diferentes curvas
        colors = ['#1f77b4', '#ff7f0e']
        
        for idx, curve_num in enumerate(target_curves):
            if curve_num not in self.curves_data:
                continue
            
            curve_data = self.curves_data[curve_num]
            color = colors[idx % len(colors)]
            label = f"{curve_data['name']} ({curve_data['angle']})"
            
            if tipo == "P-M2":
                ax.plot(curve_data['M2'], curve_data['P'], '-o', 
                       color=color, linewidth=2, markersize=4, label=label)
                ax.set_xlabel('M2', fontsize=11)
                ax.set_ylabel('P', fontsize=11)
                title = 'Diagrama de Interacción P vs M2'
            else:  # P-M3
                ax.plot(curve_data['M3'], curve_data['P'], '-o', 
                       color=color, linewidth=2, markersize=4, label=label)
                ax.set_xlabel('M3', fontsize=11)
                ax.set_ylabel('P', fontsize=11)
                title = 'Diagrama de Interacción P vs M3'
        
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.axhline(0, color='black', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='black', linewidth=0.5, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def plot_simple(self, data, tipo):
        """Genera el gráfico para formato simple."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if tipo == "P-M2":
            x_data, y_data = data['M2'], data['P']
            x_label, y_label = 'M2', 'P'
            title = 'Diagrama de Interacción P vs M2'
        else:  # P-M3
            x_data, y_data = data['M3'], data['P']
            x_label, y_label = 'M3', 'P'
            title = 'Diagrama de Interacción P vs M3'
        
        ax.plot(x_data, y_data, 'ro-', linewidth=2, markersize=5)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xlabel(x_label, fontsize=11)
        ax.set_ylabel(y_label, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axhline(0, color='black', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='black', linewidth=0.5, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()


class SDGraficosWidget(QWidget):
    """Contenedor para gráficos de Section Designer (Momento-Curvatura y P-M2-M3)."""
    
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # TabWidget interno con dos sub-pestañas
        self.tab_widget = QTabWidget()
        
        # Sub-pestaña 1: Momento Curvatura
        self.mc_widget = MomentoCurvaturaWidget(sap_interface=self.sap_interface)
        self.tab_widget.addTab(self.mc_widget, "Momento Curvatura")
        
        # Sub-pestaña 2: P-M2-M3
        self.pm_widget = PMWidget(sap_interface=self.sap_interface)
        self.tab_widget.addTab(self.pm_widget, "P-M2-M3")
        
        main_layout.addWidget(self.tab_widget)


class MeshUtilsWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.frames_widget = FrameSectionWidget(sap_interface=sap_interface)
        self.rect_mesh_widget = RectangularMeshWidget(sap_interface=sap_interface)
        self.hole_mesh_widget = HoleMeshWidget(sap_interface=sap_interface)
        self.results_widget = ResultsTableWidget(sap_interface=sap_interface)
        self.notes_widget = NotesWidget()
        self.sd_graficos_widget = SDGraficosWidget(sap_interface=sap_interface)
        
        self.tabs.insertTab(0, self.frames_widget, "Frames")
        self.tabs.addTab(self.rect_mesh_widget, "Malla Rectangular")
        self.tabs.addTab(self.hole_mesh_widget, "Malla con Orificio")
        self.tabs.addTab(self.results_widget, "Tablas de Resultados")
        self.tabs.addTab(self.notes_widget, "Notas y Recomendaciones")
        self.tabs.addTab(self.sd_graficos_widget, "SD Graficos")
        self.tabs.setCurrentIndex(0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Utilidades SAP2000 - Modelado")
        self.resize(800, 700) # Increased width slightly for better reading
        self.setCentralWidget(MeshUtilsWidget())

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
