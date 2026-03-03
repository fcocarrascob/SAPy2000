import sys
import os
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QGroupBox, QFormLayout, QComboBox, QPushButton,
                               QTextEdit, QLineEdit, QGridLayout, QHBoxLayout)
from PySide6.QtCore import Qt

# Importar backend
try:
    from .fundaciones_backend import FundacionesBackend
except ImportError:
    try:
        from fundaciones_backend import FundacionesBackend
    except ImportError:
        sys.path.append(os.path.dirname(__file__))
        from fundaciones_backend import FundacionesBackend


class FundacionesWidget(QWidget):
    """
    Widget principal para el módulo de Fundaciones.
    """
    
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.backend = None
        
        self.init_ui()
        
        # Conectar a señal de cambio de conexión si existe sap_interface
        if self.sap_interface:
            self.sap_interface.connectionChanged.connect(self.on_connection_changed)
            # Inicializar estado
            self.on_connection_changed(self.sap_interface.is_connected())
    
    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # --- Header ---
        header = QLabel("Módulo de Fundaciones")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # --- Grupo 1: Pedestales ---
        group_pedestales = QGroupBox("1. Pedestales - Sección Rectangular con Refuerzo")
        layout_pedestales = QFormLayout()
        
        # Nombre de la sección
        self.edit_section_name = QLineEdit("PED_01")
        self.edit_section_name.setMaximumWidth(200)
        self.edit_section_name.setToolTip("Nombre único para la sección de pedestal")
        layout_pedestales.addRow("Nombre Sección:", self.edit_section_name)
        
        # Material de hormigón
        self.combo_concrete_material = QComboBox()
        self.combo_concrete_material.setEditable(True)
        self.combo_concrete_material.addItem("-- Sin conexión a SAP2000 --")
        self.combo_concrete_material.setToolTip("Material de hormigón para pedestales")
        layout_pedestales.addRow("Material Hormigón:", self.combo_concrete_material)
        
        # Material de acero de refuerzo
        self.combo_rebar_material = QComboBox()
        self.combo_rebar_material.setEditable(True)
        self.combo_rebar_material.addItem("-- Sin conexión a SAP2000 --")
        self.combo_rebar_material.setToolTip("Material de acero para barras de refuerzo")
        layout_pedestales.addRow("Material Acero:", self.combo_rebar_material)
        
        # Botón para recargar materiales
        self.btn_reload_materials = QPushButton("🔄 Actualizar Materiales")
        self.btn_reload_materials.clicked.connect(self.load_materials)
        self.btn_reload_materials.setEnabled(False)
        layout_pedestales.addRow("", self.btn_reload_materials)
        
        # --- Geometría ---
        layout_pedestales.addRow(QLabel(""))  # Separador
        label_geom = QLabel("Geometría:")
        label_geom.setStyleSheet("font-weight: bold;")
        layout_pedestales.addRow(label_geom)
        
        # Dimensiones en una fila horizontal
        layout_dims = QHBoxLayout()
        
        self.edit_width = QLineEdit("500")
        self.edit_width.setMaximumWidth(100)
        self.edit_width.setToolTip("Ancho de la sección en mm")
        layout_dims.addWidget(QLabel("Ancho (mm):"))
        layout_dims.addWidget(self.edit_width)
        layout_dims.addSpacing(20)
        
        self.edit_height = QLineEdit("500")
        self.edit_height.setMaximumWidth(100)
        self.edit_height.setToolTip("Alto de la sección en mm")
        layout_dims.addWidget(QLabel("Alto (mm):"))
        layout_dims.addWidget(self.edit_height)
        layout_dims.addStretch()
        
        layout_pedestales.addRow("", layout_dims)
        
        # --- Refuerzo ---
        layout_pedestales.addRow(QLabel(""))  # Separador
        label_reinf = QLabel("Refuerzo:")
        label_reinf.setStyleSheet("font-weight: bold;")
        layout_pedestales.addRow(label_reinf)
        
        # Barras en esquinas
        self.combo_corner_bars = QComboBox()
        self.combo_corner_bars.setEditable(True)
        # Valores por defecto (se actualizarán al conectar con SAP2000)
        default_bar_sizes = ["12mm", "16mm", "20mm", "25mm", "32mm", "#6", "#8", "#10", "#11"]
        self.combo_corner_bars.addItems(default_bar_sizes)
        self.combo_corner_bars.setCurrentText("16mm")
        self.combo_corner_bars.setToolTip("Tamaño de barras en las 4 esquinas. Se actualiza con rebars del modelo al conectar.")
        layout_pedestales.addRow("Barras Esquinas:", self.combo_corner_bars)
        
        # Barras en bordes
        self.combo_edge_bars = QComboBox()
        self.combo_edge_bars.setEditable(True)
        self.combo_edge_bars.addItems(default_bar_sizes)
        self.combo_edge_bars.setCurrentText("12mm")
        self.combo_edge_bars.setToolTip("Tamaño de barras distribuidas en los 4 bordes. Se actualiza con rebars del modelo al conectar.")
        layout_pedestales.addRow("Barras Bordes:", self.combo_edge_bars)
        
        # Espaciamiento y recubrimiento en una fila
        layout_spacing = QHBoxLayout()
        
        self.edit_spacing = QLineEdit("150")
        self.edit_spacing.setMaximumWidth(100)
        self.edit_spacing.setToolTip("Espaciamiento máximo centro a centro en bordes (mm)")
        layout_spacing.addWidget(QLabel("Espaciamiento (mm):"))
        layout_spacing.addWidget(self.edit_spacing)
        layout_spacing.addSpacing(20)
        
        self.edit_cover = QLineEdit("30")
        self.edit_cover.setMaximumWidth(100)
        self.edit_cover.setToolTip("Recubrimiento de concreto (mm)")
        layout_spacing.addWidget(QLabel("Recubrimiento (mm):"))
        layout_spacing.addWidget(self.edit_cover)
        layout_spacing.addStretch()
        
        layout_pedestales.addRow("", layout_spacing)
        
        # Botón crear sección
        self.btn_create_section = QPushButton("✨ Crear Sección en Section Designer")
        self.btn_create_section.clicked.connect(self.create_pedestal_section)
        self.btn_create_section.setEnabled(False)
        self.btn_create_section.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        layout_pedestales.addRow("", self.btn_create_section)
        
        group_pedestales.setLayout(layout_pedestales)
        layout.addWidget(group_pedestales)
        
        # --- Log Area ---
        group_log = QGroupBox("Log de Operaciones")
        layout_log = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout_log.addWidget(self.log_text)
        
        group_log.setLayout(layout_log)
        layout.addWidget(group_log)
        
        # Spacer
        layout.addStretch()
        
        self.log("Módulo de Fundaciones iniciado")
        self.log("Conecte a SAP2000 para cargar materiales")
    
    def on_connection_changed(self, connected):
        """
        Se ejecuta cuando cambia el estado de conexión con SAP2000.
        
        Args:
            connected (bool): True si está conectado, False si no
        """
        self.btn_reload_materials.setEnabled(connected)
        self.btn_create_section.setEnabled(connected)
        
        if connected:
            self.log("✓ Conectado a SAP2000")
            # Cargar materiales automáticamente al conectar
            self.load_materials()
        else:
            self.log("⚠️ Desconectado de SAP2000")
            self.combo_concrete_material.clear()
            self.combo_concrete_material.addItem("-- Sin conexión a SAP2000 --")
            self.combo_rebar_material.clear()
            self.combo_rebar_material.addItem("-- Sin conexión a SAP2000 --")
            
            # Resetear combos de barras a valores por defecto
            default_sizes = ["12mm", "16mm", "20mm", "25mm", "#6", "#8", "#10"]
            self.combo_corner_bars.clear()
            self.combo_corner_bars.addItems(default_sizes)
            self.combo_corner_bars.setCurrentText("16mm")
            self.combo_edge_bars.clear()
            self.combo_edge_bars.addItems(default_sizes)
            self.combo_edge_bars.setCurrentText("12mm")
    
    def load_materials(self):
        """Carga los materiales de hormigón y acero desde el modelo SAP2000."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
                self.log("Backend de fundaciones creado")
            
            # --- Cargar materiales de concreto ---
            self.log("Obteniendo materiales de hormigón del modelo...")
            concrete_mats = self.backend.get_concrete_materials()
            
            # Guardar selección actual
            current_concrete = self.combo_concrete_material.currentText()
            
            # Actualizar combo de concreto
            self.combo_concrete_material.clear()
            
            if concrete_mats:
                for mat_name in concrete_mats:
                    self.combo_concrete_material.addItem(mat_name)
                
                # Restaurar selección previa si existe
                idx = self.combo_concrete_material.findText(current_concrete)
                if idx >= 0:
                    self.combo_concrete_material.setCurrentIndex(idx)
                else:
                    self.combo_concrete_material.setCurrentIndex(0)
                
                self.log(f"✓ {len(concrete_mats)} materiales de hormigón encontrados")
            else:
                self.combo_concrete_material.addItem("-- No hay materiales de hormigón --")
                self.log("⚠️ No se encontraron materiales de hormigón en el modelo")
            
            # --- Cargar materiales de acero de refuerzo ---
            self.log("Obteniendo materiales de acero de refuerzo...")
            rebar_mats = self.backend.get_rebar_materials()
            
            # Guardar selección actual
            current_rebar = self.combo_rebar_material.currentText()
            
            # Actualizar combo de rebar
            self.combo_rebar_material.clear()
            
            if rebar_mats:
                for mat_name in rebar_mats:
                    self.combo_rebar_material.addItem(mat_name)
                
                # Restaurar selección previa si existe
                idx = self.combo_rebar_material.findText(current_rebar)
                if idx >= 0:
                    self.combo_rebar_material.setCurrentIndex(idx)
                else:
                    self.combo_rebar_material.setCurrentIndex(0)
                
                self.log(f"✓ {len(rebar_mats)} materiales de acero encontrados")
            else:
                self.combo_rebar_material.addItem("-- No hay materiales de acero --")
                self.log("⚠️ No se encontraron materiales de acero en el modelo")
            
            # --- Cargar tamaños de barras (rebar sizes) ---
            self.log("Obteniendo tamaños de barras definidos...")
            rebar_sizes = self.backend.get_rebar_sizes()
            
            # Guardar selecciones actuales
            current_corner = self.combo_corner_bars.currentText()
            current_edge = self.combo_edge_bars.currentText()
            
            # Actualizar combos de barras
            self.combo_corner_bars.clear()
            self.combo_edge_bars.clear()
            
            if rebar_sizes:
                # Agregar los rebars del modelo
                for rebar_name in rebar_sizes:
                    self.combo_corner_bars.addItem(rebar_name)
                    self.combo_edge_bars.addItem(rebar_name)
                
                # Restaurar selecciones previas si existen
                idx_corner = self.combo_corner_bars.findText(current_corner)
                if idx_corner >= 0:
                    self.combo_corner_bars.setCurrentIndex(idx_corner)
                else:
                    self.combo_corner_bars.setCurrentIndex(0)
                
                idx_edge = self.combo_edge_bars.findText(current_edge)
                if idx_edge >= 0:
                    self.combo_edge_bars.setCurrentIndex(idx_edge)
                else:
                    self.combo_edge_bars.setCurrentIndex(0)
                
                self.log(f"✓ {len(rebar_sizes)} tamaños de barras encontrados: {', '.join(rebar_sizes[:5])}{'...' if len(rebar_sizes) > 5 else ''}")
            else:
                # Si no hay rebars definidos, usar valores por defecto
                default_sizes = ["12mm", "16mm", "20mm", "25mm", "#6", "#8", "#10"]
                self.combo_corner_bars.addItems(default_sizes)
                self.combo_edge_bars.addItems(default_sizes)
                self.combo_corner_bars.setCurrentText("16mm")
                self.combo_edge_bars.setCurrentText("12mm")
                self.log("⚠️ No se encontraron rebars definidos. Usando valores por defecto.")
                self.log("   Puede definir rebars en SAP2000: Define > Section Properties > Reinforcing Bars")
                
        except Exception as e:
            self.log(f"❌ Error cargando materiales: {e}")
            import traceback
            traceback.print_exc()
    
    def create_pedestal_section(self):
        """Crea una sección de pedestal rectangular con refuerzo en Section Designer."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
            
            # Obtener valores de los inputs
            section_name = self.edit_section_name.text().strip()
            concrete_mat = self.combo_concrete_material.currentText().strip()
            rebar_mat = self.combo_rebar_material.currentText().strip()
            
            # Validaciones
            if not section_name:
                self.log("❌ Debe especificar un nombre para la sección")
                return
            
            if "--" in concrete_mat or not concrete_mat:
                self.log("❌ Debe seleccionar un material de hormigón válido")
                return
            
            if "--" in rebar_mat or not rebar_mat:
                self.log("❌ Debe seleccionar un material de acero válido")
                return
            
            # Convertir dimensiones a float
            try:
                width = float(self.edit_width.text())
                height = float(self.edit_height.text())
                spacing = float(self.edit_spacing.text())
                cover = float(self.edit_cover.text())
            except ValueError:
                self.log("❌ Las dimensiones deben ser valores numéricos")
                return
            
            # Validar dimensiones positivas
            if width <= 0 or height <= 0:
                self.log("❌ Las dimensiones deben ser mayores a cero")
                return
            
            if spacing <= 0 or cover < 0:
                self.log("❌ Espaciamiento debe ser positivo y recubrimiento no negativo")
                return
            
            corner_bar = self.combo_corner_bars.currentText().strip()
            edge_bar = self.combo_edge_bars.currentText().strip()
            
            if not corner_bar or not edge_bar:
                self.log("❌ Debe especificar los tamaños de barras")
                return
            
            # Log de inicio
            self.log("=" * 60)
            self.log(f"Creando sección: {section_name}")
            self.log(f"  Concreto: {concrete_mat}")
            self.log(f"  Acero: {rebar_mat}")
            self.log(f"  Geometría: {width} x {height} mm")
            self.log(f"  Refuerzo esquinas: {corner_bar}")
            self.log(f"  Refuerzo bordes: {edge_bar} @ {spacing} mm")
            self.log(f"  Recubrimiento: {cover} mm")
            self.log("-" * 60)
            
            # Llamar al backend para crear la sección
            success = self.backend.create_rectangular_pedestal_section(
                section_name=section_name,
                concrete_mat=concrete_mat,
                rebar_mat=rebar_mat,
                width=width,
                height=height,
                corner_bar_size=corner_bar,
                edge_bar_size=edge_bar,
                edge_spacing=spacing,
                cover=cover
            )
            
            if success:
                self.log("=" * 60)
                self.log(f"✅ Sección {section_name} creada exitosamente!")
                self.log("   Revise el Section Designer en SAP2000")
                self.log("=" * 60)
                
                # Incrementar nombre para próxima sección
                # Extraer número al final si existe
                import re
                match = re.search(r'(\d+)$', section_name)
                if match:
                    num = int(match.group(1))
                    base_name = section_name[:match.start()]
                    next_name = f"{base_name}{num + 1:02d}"
                    self.edit_section_name.setText(next_name)
            else:
                self.log("❌ Error al crear la sección. Revise el log para detalles")
                
        except Exception as e:
            self.log(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def load_concrete_materials(self):
        """DEPRECATED: Use load_materials() instead."""
        self.load_materials()
    
    def log(self, message):
        """Agrega un mensaje al log."""
        self.log_text.append(message)


# Ejecución standalone
if __name__ == "__main__":
    print("Ejecutando Fundaciones GUI en modo standalone...")
    
    app = QApplication(sys.argv)
    
    # Crear widget sin sap_interface (se conectará vía GetActiveObject en backend)
    window = FundacionesWidget()
    window.setWindowTitle("Fundaciones - Modo Standalone")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
