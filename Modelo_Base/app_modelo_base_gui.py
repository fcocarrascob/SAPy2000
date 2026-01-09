"""Interfaz gráfica para el módulo de Creación de Modelo Base.

Replica el diseño de la referencia con parámetros sísmicos NCh detallados.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QMessageBox, QGridLayout, QSpacerItem, QSizePolicy,
    QFrame, QProgressBar, QDialog, QSplitter, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QColor

# Importar matplotlib para preview del espectro
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


from .modelo_base_backend import BaseModelBackend, BaseModelResult
from .config import AR_BY_ZONE, SOIL_PARAMS, GRAVITY


class CreateModelWorker(QThread):
    """Worker thread para crear el modelo base sin bloquear la GUI."""
    finished = Signal(object)  # BaseModelResult
    progress = Signal(int, str)  # (percent, message)
    
    def __init__(self, backend: BaseModelBackend, params: dict):
        super().__init__()
        self.backend = backend
        self.params = params
    
    def run(self):
        result = self.backend.create_base_model(
            **self.params,
            progress_callback=self._report_progress
        )
        self.finished.emit(result)
    
    def _report_progress(self, pct: int, msg: str):
        self.progress.emit(pct, msg)


class SpectrumPreviewDialog(QDialog):
    """Diálogo emergente para mostrar gráfico y tabla del espectro."""
    def __init__(self, parent=None, data_dict=None, params_text=""):
        super().__init__(parent)
        self.setWindowTitle("Vista Previa Espectro NCh433")
        self.resize(1100, 650)
        self.setModal(True)
        
        # data_dict keys: T, Sax, Say, Sav, Rx, Ry, Rv...
        self.data = data_dict or {}
        self.params_text = params_text
        
        self.init_ui()
        self.plot_data()
        self.fill_table()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # --- Panel Izquierdo (Tabla y Params) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Grupo Parámetros
        grp_params = QGroupBox("Parámetros Definidos")
        grp_layout = QVBoxLayout(grp_params)
        lbl_params = QLabel(self.params_text)
        lbl_params.setWordWrap(True)
        lbl_params.setStyleSheet("font-family: Consolas; font-size: 11px;")
        grp_layout.addWidget(lbl_params)
        left_layout.addWidget(grp_params)
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["T [s]", "Sa X [g]", "Sa Y [g]", "Sa V [g]"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.table)
        
        splitter.addWidget(left_widget)
        
        # --- Panel Derecho (Gráfico) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(6, 5), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)
            
            right_layout.addWidget(self.toolbar)
            right_layout.addWidget(self.canvas)
        else:
            right_layout.addWidget(QLabel("Matplotlib no instalado."))
            
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (35% left, 65% right)
        splitter.setSizes([350, 650])
        
        # Botón Cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("padding: 5px 20px;")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def plot_data(self):
        if not MATPLOTLIB_AVAILABLE or not self.data:
            return
            
        T = self.data.get('T', [])
        Sax = self.data.get('Sax', [])
        Say = self.data.get('Say', [])
        Sav = self.data.get('Sav', [])
        
        ax = self.figure.add_subplot(111)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        if Sax:
            ax.plot(T, Sax, 'b-', linewidth=1.5, label=f"Horizontal X (R={self.data.get('Rx',0)})")
        if Say:
            # Check if different from X to avoid clutter, or just plot if exists
            # Logic handled by caller passed data
            if self.data.get('has_y', False):
                ax.plot(T, Say, 'g-.', linewidth=1.5, label=f"Horizontal Y (R={self.data.get('Ry',0)})")
        if Sav:
            ax.plot(T, Sav, 'r--', linewidth=1.5, label=f"Vertical (R={self.data.get('Rv',0)})")
            
        ax.set_xlabel("Period $T$ [s]")
        ax.set_ylabel("Spectral Acceleration $S_a$ [g]")
        ax.set_title("Espectro de Diseño NCh433 Ref.")
        ax.legend()
        
        self.canvas.draw()

    def fill_table(self):
        T = self.data.get('T', [])
        if len(T) == 0:
            return
            
        Sax = self.data.get('Sax', [])
        Say = self.data.get('Say', [])
        Sav = self.data.get('Sav', [])
        
        rows = len(T)
        self.table.setRowCount(rows)
        self.table.setUpdatesEnabled(False) # Optimization
        
        try:
            for i in range(rows):
                # T
                item_t = QTableWidgetItem(f"{T[i]:.3f}")
                item_t.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 0, item_t)
                
                # Sax
                val_x = Sax[i] if i < len(Sax) else 0.0
                item_x = QTableWidgetItem(f"{val_x:.4f}")
                item_x.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 1, item_x)
                
                # Say
                val_y = Say[i] if i < len(Say) else 0.0
                item_y = QTableWidgetItem(f"{val_y:.4f}")
                item_y.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 2, item_y)
                
                # Sav
                val_v = Sav[i] if i < len(Sav) else 0.0
                item_v = QTableWidgetItem(f"{val_v:.4f}")
                item_v.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 3, item_v)
        finally:
            self.table.setUpdatesEnabled(True)


class ModeloBaseWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.backend = None 
        self.worker = None
        
        self.init_ui()

    def init_ui(self):
        # Layout Principal
        main_layout = QVBoxLayout(self)
        
        # --- Grupo: Base Model (Inputs) ---
        self.base_model_group = QGroupBox("Parámetros del Modelo Base")
        # Layout vertical para el grupo (contendrá inputs + botones + chart)
        group_layout = QVBoxLayout(self.base_model_group)
        
        # 1. Widget de Inputs (Grid)
        self.inputs_widget = QWidget()
        grid = QGridLayout(self.inputs_widget)
        grid.setColumnStretch(1, 1) # Estirar columna de inputs

        # -- Fila 0: Zona Sísmica --
        self.lbl_zone = QLabel("Zona Sísmica:")
        self.combo_zone = QComboBox()
        self.combo_zone.addItems(["1", "2", "3"])
        grid.addWidget(self.lbl_zone, 0, 0)
        grid.addWidget(self.combo_zone, 0, 1)

        # -- Fila 1: Tipo de Suelo --
        self.lbl_soil = QLabel("Tipo de Suelo:")
        self.combo_soil = QComboBox()
        self.combo_soil.addItems(["A", "B", "C", "D", "E"])
        grid.addWidget(self.lbl_soil, 1, 0)
        grid.addWidget(self.combo_soil, 1, 1)

        # -- Fila 2: Factor de Importancia --
        self.lbl_importance = QLabel("Factor de Importancia (I):")
        self.spin_importance = QDoubleSpinBox()
        self.spin_importance.setDecimals(2)
        self.spin_importance.setRange(0.1, 5.0)
        self.spin_importance.setSingleStep(0.1)
        self.spin_importance.setValue(1.0)
        grid.addWidget(self.lbl_importance, 2, 0)
        grid.addWidget(self.spin_importance, 2, 1)

        # -- Fila 3: Separador / Título Horizontal --
        self.lbl_horiz_title = QLabel("--- Parámetros Horizontales ---")
        font_bold = QFont()
        font_bold.setBold(True)
        self.lbl_horiz_title.setFont(font_bold)
        self.lbl_horiz_title.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_horiz_title, 3, 0, 1, 2)

        # -- Fila 4: Amortiguamiento X --
        self.lbl_damp_x = QLabel("Amortiguamiento X (ξx):")
        self.spin_damp_x = QDoubleSpinBox()
        self.spin_damp_x.setDecimals(3)
        self.spin_damp_x.setRange(0.001, 0.2)
        self.spin_damp_x.setSingleStep(0.001)
        self.spin_damp_x.setValue(0.03)
        grid.addWidget(self.lbl_damp_x, 4, 0)
        grid.addWidget(self.spin_damp_x, 4, 1)

        # -- Fila 5: Factor Rx --
        self.lbl_R_x = QLabel("Factor Rx:")
        self.spin_R_x = QDoubleSpinBox()
        self.spin_R_x.setDecimals(2)
        self.spin_R_x.setRange(1.0, 12.0)
        self.spin_R_x.setSingleStep(0.1)
        self.spin_R_x.setValue(3.0)
        grid.addWidget(self.lbl_R_x, 5, 0)
        grid.addWidget(self.spin_R_x, 5, 1)

        # -- Fila 6: Amortiguamiento Y --
        self.lbl_damp_y = QLabel("Amortiguamiento Y (ξy):")
        self.spin_damp_y = QDoubleSpinBox()
        self.spin_damp_y.setDecimals(3)
        self.spin_damp_y.setRange(0.001, 0.2)
        self.spin_damp_y.setSingleStep(0.001)
        self.spin_damp_y.setValue(0.03)
        grid.addWidget(self.lbl_damp_y, 6, 0)
        grid.addWidget(self.spin_damp_y, 6, 1)

        # -- Fila 7: Factor Ry --
        self.lbl_R_y = QLabel("Factor Ry:")
        self.spin_R_y = QDoubleSpinBox()
        self.spin_R_y.setDecimals(2)
        self.spin_R_y.setRange(1.0, 12.0)
        self.spin_R_y.setSingleStep(0.1)
        self.spin_R_y.setValue(3.0)
        grid.addWidget(self.lbl_R_y, 7, 0)
        grid.addWidget(self.spin_R_y, 7, 1)

        # -- Fila 8: Separador / Título Vertical --
        self.lbl_vert_title = QLabel("--- Parámetros Verticales ---")
        self.lbl_vert_title.setFont(font_bold)
        self.lbl_vert_title.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_vert_title, 8, 0, 1, 2)

        # -- Fila 9: Amortiguamiento Vertical --
        self.lbl_vert_damp = QLabel("Amortiguamiento Vertical (ξv):")
        self.spin_vert_damp = QDoubleSpinBox()
        self.spin_vert_damp.setDecimals(3)
        self.spin_vert_damp.setRange(0.001, 0.2)
        self.spin_vert_damp.setSingleStep(0.001)
        self.spin_vert_damp.setValue(0.03)
        grid.addWidget(self.lbl_vert_damp, 9, 0)
        grid.addWidget(self.spin_vert_damp, 9, 1)

        # -- Fila 10: R Vertical --
        self.lbl_vert_R = QLabel("Factor R (Vertical):")
        self.spin_vert_R = QDoubleSpinBox()
        self.spin_vert_R.setDecimals(2)
        self.spin_vert_R.setRange(1.0, 12.0)
        self.spin_vert_R.setSingleStep(0.1)
        self.spin_vert_R.setValue(2.0) 
        grid.addWidget(self.lbl_vert_R, 10, 0)
        grid.addWidget(self.spin_vert_R, 10, 1)

        group_layout.addWidget(self.inputs_widget)

        # 2. Botones
        self.buttons_widget = QWidget()
        btn_layout = QHBoxLayout(self.buttons_widget)
        
        self.btn_preview_spectrum = QPushButton("Generar Vista Previa Espectro")
        self.btn_preview_spectrum.setEnabled(MATPLOTLIB_AVAILABLE)
        if not MATPLOTLIB_AVAILABLE:
            self.btn_preview_spectrum.setToolTip("Instalar matplotlib para habilitar: pip install matplotlib")
        else:
            self.btn_preview_spectrum.clicked.connect(self.on_preview_spectrum_click)

        self.btn_create_model = QPushButton("Crear Modelo Base")
        self.btn_create_model.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px;")
        self.btn_create_model.clicked.connect(self.on_create_model_click)

        btn_layout.addWidget(self.btn_preview_spectrum)
        btn_layout.addWidget(self.btn_create_model)
        
        group_layout.addWidget(self.buttons_widget)
        
        # 3. Barra de Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        group_layout.addWidget(self.progress_bar)
        
        # 4. Label de Estado
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #666; font-style: italic;")
        group_layout.addWidget(self.lbl_status)
        
        # (Gráfico eliminado de la interfaz principal, ahora es un pop-up)

        # Spacer final
        main_layout.addWidget(self.base_model_group)
        main_layout.addStretch()

    def on_create_model_click(self):
        """Manejador para crear el modelo."""
        # Validar conexión
        if not self.sap_interface or not self.sap_interface.SapModel:
            QMessageBox.warning(self, "Desconectado", "No hay conexión activa con SAP2000.")
            return

        # Confirmación
        res = QMessageBox.warning(
            self, "Advertencia", 
            "Esto BORRARÁ el modelo actual y creará uno nuevo.\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if res != QMessageBox.Yes:
            return

        # Leer parámetros GUI
        try:
            params = {
                "zone": int(self.combo_zone.currentText()),
                "soil": self.combo_soil.currentText(),
                "r_x": self.spin_R_x.value(),
                "r_y": self.spin_R_y.value(),
                "importance": self.spin_importance.value(),
                "damping": self.spin_damp_x.value(),
                "damping_y": self.spin_damp_y.value(),
                "xi_v": self.spin_vert_damp.value(),
                "r_v": self.spin_vert_R.value(),
            }
            
            # Instanciar Backend
            self.backend = BaseModelBackend(self.sap_interface.SapModel)
            
            # Preparar UI para ejecución
            self.btn_create_model.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.lbl_status.setText("Iniciando...")
            
            # Ejecutar en thread separado
            self.worker = CreateModelWorker(self.backend, params)
            self.worker.progress.connect(self._on_progress)
            self.worker.finished.connect(self._on_finished)
            self.worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Excepción", f"Ocurrió un error inesperado:\n{str(e)}")
            self._reset_ui()

    def _on_progress(self, pct: int, msg: str):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def _on_finished(self, result: BaseModelResult):
        """Maneja la finalización de la creación."""
        self._reset_ui()
        
        if result.success:
            QMessageBox.information(self, "Éxito", result.message)
        else:
            error_detail = "\n".join(result.errors) if result.errors else result.message
            QMessageBox.critical(self, "Error", f"Falló la creación:\n{error_detail}")

    def _reset_ui(self):
        """Restaura la UI tras la ejecución."""
        self.btn_create_model.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("")

    def on_preview_spectrum_click(self):
        """Genera la vista previa del espectro en una ventana emergente."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        try:
            # Leer parámetros de la GUI
            zone = int(self.combo_zone.currentText())
            soil = self.combo_soil.currentText()
            R_x = self.spin_R_x.value()
            R_y = self.spin_R_y.value()
            I = self.spin_importance.value()
            xi_x = self.spin_damp_x.value()
            xi_y = self.spin_damp_y.value()
            R_v = self.spin_vert_R.value()
            xi_v = self.spin_vert_damp.value()
            
            # Calcular espectros
            T_vals, Sa_x, Sa_y, Sa_vert = self._compute_spectrum_preview(
                zone, soil, R_x, R_y, I, xi_x, xi_y, R_v, xi_v
            )
            
            # Preparar datos para el diálogo
            data_dict = {
                'T': T_vals,
                'Sax': Sa_x,
                'Say': Sa_y,
                'Sav': Sa_vert,
                'Rx': R_x,
                'Ry': R_y,
                'Rv': R_v,
                'has_y': (abs(R_x - R_y) > 0.01) or (abs(xi_x - xi_y) > 0.001)
            }
            
            # Texto resumen de parámetros
            params_info = (
                f"Zona Sísmica: {zone}\n"
                f"Suelo: {soil}\n"
                f"I: {I:.2f}\n\n"
                f"H-X: Rx={R_x}, ξ={xi_x}\n"
                f"H-Y: Ry={R_y}, ξ={xi_y}\n"
                f"Vert: Rv={R_v}, ξ={xi_v}"
            )
            
            # Abrir diálogo
            dlg = SpectrumPreviewDialog(self, data_dict, params_info)
            dlg.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "Error Preview", f"No se pudo generar el espectro:\n{str(e)}")

    def _compute_spectrum_preview(self, zone: int, soil: str, R_x: float, R_y: float, I: float, 
                                   xi_x: float, xi_y: float, R_v: float, xi_v: float):
        """Calcula el espectro replicando EXACTAMENTE la lógica del Backend (NCh Unified)."""
        import numpy as np
        
        # Parámetros de suelo (Valores deben coincidir con config.py)
        sp = SOIL_PARAMS[soil]
        s, r, t0, p_exp, q_exp, t1 = sp.S, sp.r, sp.T0, sp.p, sp.q, sp.T1
        ar = AR_BY_ZONE[zone]
        
        # Generar períodos
        T_vals = np.arange(0.0, 5.01, 0.01)
        
        Sa_x = []
        Sa_y = []
        Sa_vert = []
        
        for T in T_vals:
            # --- Common Shape Calculation (Unified Formula) ---
            # Horizontal Shape Base
            ratio = (T / t0) if t0 > 0 else 0
            if T == 0:
                sah_base = ar * s
            else:
                num = 1.0 + r * (ratio ** p_exp)
                den = 1.0 + (ratio ** q_exp)
                sah_base = ar * s * num / den

            # --- R* Calculation Logic (Copied from Backend) ---
            def get_r_star(R_val, T_val, t1_val):
                cr = 0.16 * R_val
                limit = cr * t1_val
                
                if limit <= 0:
                    return R_val
                elif T_val >= limit:
                    return R_val
                else:
                    # Interpolación lineal 1.5 -> R
                    ratio_t = T_val / limit
                    return 1.5 + (R_val - 1.5) * ratio_t

            # --- Horizontal X ---
            r_star_x = get_r_star(R_x, T, t1)
            damping_scale_x = (0.05 / xi_x) ** 0.4 if xi_x > 0 else 1.0
            val_x = I * sah_base * damping_scale_x / r_star_x
            Sa_x.append(val_x)

            # --- Horizontal Y ---
            r_star_y = get_r_star(R_y, T, t1)
            damping_scale_y = (0.05 / xi_y) ** 0.4 if xi_y > 0 else 1.0
            val_y = I * sah_base * damping_scale_y / r_star_y
            Sa_y.append(val_y)
            
            # --- Vertical Spectrum (Copied from Backend) ---
            # "La fórmula del espectro vertical usa un período desplazado (1.7×T)
            # y un factor de escala de 0.7 respecto al horizontal."
            
            vertical_factor = 0.7
            period_shift = 1.7
            T_shifted = period_shift * T
            
            ratio_v = (T_shifted / t0) if t0 > 0 else 0
            
            if T == 0:
                sav_base = vertical_factor * ar * s
            else:
                num_v = 1.0 + r * (ratio_v ** p_exp)
                den_v = 1.0 + (ratio_v ** q_exp)
                sav_base = vertical_factor * ar * s * num_v / den_v
            
            # Vertical NO usa R* (usa reducción directa R_v)
            damping_scale_v = (0.05 / xi_v) ** 0.4 if xi_v > 0 else 1.0
            val_v = I * sav_base * damping_scale_v / R_v
            Sa_vert.append(val_v)
        
        return T_vals, Sa_x, Sa_y, Sa_vert
    
    # Métodos auxiliares eliminados ya que la lógica está integrada arriba para garantizar paridad.

        """Calcula el factor de amplificación α según NCh433."""
        if T <= T0:
            # Rama ascendente: α = 1 + T/T0 * (2.75-1)
            return 1.0 + (T / T0) * 1.75 if T0 > 0 else 2.75
        else:
            # Rama descendente: α = 2.75 * (T0/T)^p
            return 2.75 * (T0 / T) ** p

    def _calc_alpha_vertical(self, T: float, T0: float, p: float, q: float) -> float:
        """Calcula el factor de amplificación α vertical (sin factor r)."""
        Tv0 = T0 * 0.7  # Período vertical típico más corto
        if T <= Tv0:
            return 1.0 + (T / Tv0) * 1.5 if Tv0 > 0 else 2.5
        else:
            return 2.5 * (Tv0 / T) ** p
