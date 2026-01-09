"""Interfaz gráfica para el módulo de Creación de Modelo Base.

Replica el diseño de la referencia con parámetros sísmicos NCh detallados.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QDoubleSpinBox, QPushButton, QGroupBox,
    QMessageBox, QGridLayout, QSpacerItem, QSizePolicy,
    QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

# Importar matplotlib para preview del espectro
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
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

        # -- Fila 4: Amortiguamiento Horizontal --
        self.lbl_damp = QLabel("Amortiguamiento (ξ):")
        self.spin_damp = QDoubleSpinBox()
        self.spin_damp.setDecimals(3)
        self.spin_damp.setRange(0.001, 0.2)
        self.spin_damp.setSingleStep(0.001)
        self.spin_damp.setValue(0.050) # Usualmente 0.05, referencia dice 0.03 default
        # Ajustamos al valor de referencia
        self.spin_damp.setValue(0.050) 
        grid.addWidget(self.lbl_damp, 4, 0)
        grid.addWidget(self.spin_damp, 4, 1)

        # -- Fila 5: R Horizontal --
        self.lbl_R = QLabel("Factor R (Horizontal):")
        self.spin_R = QDoubleSpinBox()
        self.spin_R.setDecimals(2)
        self.spin_R.setRange(1.0, 12.0)
        self.spin_R.setSingleStep(0.1)
        self.spin_R.setValue(7.0) # Valor típico, referencia dice 3.0? Ajustamos a 7 (acero)
        grid.addWidget(self.lbl_R, 5, 0)
        grid.addWidget(self.spin_R, 5, 1)

        # -- Fila 6: Separador / Título Vertical --
        self.lbl_vert_title = QLabel("--- Parámetros Verticales ---")
        self.lbl_vert_title.setFont(font_bold)
        self.lbl_vert_title.setAlignment(Qt.AlignCenter)
        grid.addWidget(self.lbl_vert_title, 6, 0, 1, 2)

        # -- Fila 7: Amortiguamiento Vertical --
        self.lbl_vert_damp = QLabel("Amortiguamiento Vertical (ξv):")
        self.spin_vert_damp = QDoubleSpinBox()
        self.spin_vert_damp.setDecimals(3)
        self.spin_vert_damp.setRange(0.001, 0.2)
        self.spin_vert_damp.setSingleStep(0.001)
        self.spin_vert_damp.setValue(0.050)
        grid.addWidget(self.lbl_vert_damp, 7, 0)
        grid.addWidget(self.spin_vert_damp, 7, 1)

        # -- Fila 8: R Vertical --
        self.lbl_vert_R = QLabel("Factor R (Vertical):")
        self.spin_vert_R = QDoubleSpinBox()
        self.spin_vert_R.setDecimals(2)
        self.spin_vert_R.setRange(1.0, 12.0)
        self.spin_vert_R.setSingleStep(0.1)
        self.spin_vert_R.setValue(7.0) 
        grid.addWidget(self.lbl_vert_R, 8, 0)
        grid.addWidget(self.spin_vert_R, 8, 1)

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
        
        # 5. Placeholder para Gráfico (o Canvas de Matplotlib)
        self.chart_frame = QFrame()
        self.chart_frame.setFrameShape(QFrame.StyledPanel)
        self.chart_frame.setMinimumHeight(250)
        self.chart_layout = QVBoxLayout(self.chart_frame)
        
        if MATPLOTLIB_AVAILABLE:
            # Canvas de Matplotlib
            self.figure = Figure(figsize=(5, 3), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.chart_layout.addWidget(self.canvas)
        else:
            self.lbl_chart_placeholder = QLabel("Vista Previa del Espectro (matplotlib no disponible)")
            self.lbl_chart_placeholder.setAlignment(Qt.AlignCenter)
            self.lbl_chart_placeholder.setStyleSheet("color: gray; font-style: italic;")
            self.chart_layout.addWidget(self.lbl_chart_placeholder)
        
        group_layout.addWidget(self.chart_frame)

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
                "r_x": self.spin_R.value(),
                "r_y": self.spin_R.value(),  # Usar mismo R para X e Y
                "importance": self.spin_importance.value(),
                "damping": self.spin_damp.value(),
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
        """Genera la vista previa del espectro NCh433 con parámetros actuales."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        try:
            # Leer parámetros de la GUI
            zone = int(self.combo_zone.currentText())
            soil = self.combo_soil.currentText()
            R = self.spin_R.value()
            I = self.spin_importance.value()
            xi = self.spin_damp.value()
            R_v = self.spin_vert_R.value()
            xi_v = self.spin_vert_damp.value()
            
            # Calcular espectros
            T_vals, Sa_horiz, Sa_vert = self._compute_spectrum_preview(
                zone, soil, R, I, xi, R_v, xi_v
            )
            
            # Dibujar en el canvas
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            ax.plot(T_vals, Sa_horiz, 'b-', linewidth=1.5, label=f'Horizontal (R={R:.1f})')
            ax.plot(T_vals, Sa_vert, 'r--', linewidth=1.5, label=f'Vertical (R_v={R_v:.1f})')
            
            ax.set_xlabel('Período T [s]')
            ax.set_ylabel('Sa [g]')
            ax.set_title(f'Espectro NCh433 - Zona {zone}, Suelo {soil}, I={I:.2f}')
            ax.set_xlim(0, 5.0)
            ax.set_ylim(0, max(max(Sa_horiz), max(Sa_vert)) * 1.1)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=8)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.warning(self, "Error Preview", f"No se pudo generar el espectro:\n{str(e)}")

    def _compute_spectrum_preview(self, zone: int, soil: str, R: float, I: float, 
                                   xi: float, R_v: float, xi_v: float):
        """Calcula el espectro NCh433 para preview (sin SAP2000).
        
        Returns:
            (T_vals, Sa_horizontal, Sa_vertical) - arrays con valores del espectro
        """
        import numpy as np
        
        # Parámetros de suelo
        sp = SOIL_PARAMS[soil]
        A0 = AR_BY_ZONE[zone]
        
        # Generar períodos
        T_vals = np.arange(0.0, 5.01, 0.01)
        
        Sa_horiz = []
        Sa_vert = []
        
        for T in T_vals:
            # --- Espectro Horizontal NCh433 ---
            # Factor α según NCh433
            alpha_h = self._calc_alpha(T, sp.T0, sp.p, sp.q)
            
            # R* (factor de reducción modificado por T)
            if T > 0.10 and T < sp.T1:
                R_star = 1.0 + (R - 1.0) * (T - 0.10) / (sp.T1 - 0.10)
            elif T >= sp.T1:
                R_star = R
            else:
                R_star = 1.0
            
            # Coeficiente (ξ/5)^0.4 para amortiguamiento
            damp_factor = (xi / 0.05) ** 0.4 if xi != 0.05 else 1.0
            
            # Sa horizontal = α * A0 * S * I / R* (en g)
            Sa_h = alpha_h * A0 * sp.S * I / (R_star * damp_factor)
            Sa_horiz.append(Sa_h)
            
            # --- Espectro Vertical NCh433 ---
            # Factor α para vertical (sin considerar r)
            alpha_v = self._calc_alpha_vertical(T, sp.T0, sp.p, sp.q)
            
            # Coeficiente vertical según NCh433
            Cv = 2.0 / 3.0  # Factor vertical típico
            
            # Factor de amortiguamiento vertical
            damp_factor_v = (xi_v / 0.05) ** 0.4 if xi_v != 0.05 else 1.0
            
            # Sa vertical = Cv * α * A0 * S * I / R_v (sin R*)
            Sa_v = Cv * alpha_v * A0 * sp.S * I / (R_v * damp_factor_v)
            Sa_vert.append(Sa_v)
        
        return T_vals, Sa_horiz, Sa_vert

    def _calc_alpha(self, T: float, T0: float, p: float, q: float) -> float:
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
