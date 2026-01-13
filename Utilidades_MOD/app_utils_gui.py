import sys
import os
import math
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
                               QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                               QComboBox, QGroupBox, QGridLayout, QFormLayout, QTabWidget,
                               QTextBrowser)
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QUrl

# Importar backend
try:
    from .utils_backend import SapUtils
except ImportError:
    try:
        from utils_backend import SapUtils
    except ImportError:
        # Fallback si se ejecuta desde otro directorio
        sys.path.append(os.path.dirname(__file__))
        from utils_backend import SapUtils

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: white; border: 1px solid #999;")
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
        self.connect_btn = QPushButton("Conectar SAP2000")
        self.connect_btn.clicked.connect(self.connect_sap)
        
        self.generate_btn = QPushButton("Generar Malla")
        self.generate_btn.clicked.connect(self.generate_mesh)
        self.generate_btn.setEnabled(False) # Deshabilitado hasta conectar
        
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.generate_btn)
        layout.addLayout(btn_layout)
        
        # --- Log ---
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def log(self, message):
        if self.log_text:
            self.log_text.append(message)

    def connect_sap(self):
        self.log("Intentando conectar a SAP2000...")
        self.backend = SapUtils()
        if self.backend.SapModel:
            self.log("✅ Conectado exitosamente.")
            if self.generate_btn:
                self.generate_btn.setEnabled(True)
            try:
                filename = self.backend.SapModel.GetModelFilename()
                self.log(f"Archivo abierto: {filename}")
            except:
                pass
        else:
            self.log("❌ Error al conectar. Asegúrate de que SAP2000 esté abierto.")

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
        
        self.btn_get_coords = QPushButton("Obtener Coordenadas")
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
            
            self.log(f"Generando malla {nx}x{ny} en {plane}...")
            areas = self.backend.create_mesh_by_coord(w, l, nx, ny, sx, sy, sz, plane, prop)
            
            if areas:
                self.log(f"✅ Éxito: {len(areas)} áreas creadas.")
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
        
        self.btn_get_coords = QPushButton("Obtener Coordenadas")
        self.btn_get_coords.clicked.connect(self.fetch_coords)
        
        loc_layout.addWidget(QLabel("Propiedad Área:"), 0, 2)
        loc_layout.addWidget(self.prop_edit, 0, 3)
        loc_layout.addWidget(QLabel("Plano:"), 1, 2)
        loc_layout.addWidget(self.plane_combo, 1, 3)
        loc_layout.addWidget(self.btn_get_coords, 2, 2, 1, 2)
        
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
            
            self.log(f"Generando malla con orificio ({inner_s} en {outer_s})...")
            areas = self.backend.create_hole_mesh(
                outer_s, outer_d, inner_s, inner_d,
                n_ang, n_rad, sx, sy, sz, plane, prop
            )
            
            if areas:
                self.log(f"✅ Éxito: {len(areas)} áreas creadas.")
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


class MeshUtilsWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.rect_mesh_widget = RectangularMeshWidget(sap_interface=sap_interface)
        self.hole_mesh_widget = HoleMeshWidget(sap_interface=sap_interface)
        self.notes_widget = NotesWidget()
        
        self.tabs.addTab(self.rect_mesh_widget, "Malla Rectangular")
        self.tabs.addTab(self.hole_mesh_widget, "Malla con Orificio")
        self.tabs.addTab(self.notes_widget, "Notas y Recomendaciones")


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
