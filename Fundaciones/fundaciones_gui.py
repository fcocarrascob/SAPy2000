import sys
import os
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QGroupBox, QFormLayout, QComboBox, QPushButton,
                               QTextEdit, QLineEdit, QGridLayout, QHBoxLayout, QTabWidget)
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
        """Inicializa la interfaz de usuario con pestañas."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; }
            QTabBar::tab { padding: 8px 20px; font-weight: bold; }
            QTabBar::tab:selected { background: #3498db; color: white; }
        """)
        
        # ========== PESTAÑA 1: DEFINICIONES ==========
        tab_definiciones = QWidget()
        layout_def = QVBoxLayout(tab_definiciones)
        layout_def.setSpacing(15)
        
        # --- Materiales Compartidos ---
        group_materiales = QGroupBox("Materiales")
        layout_mat = QFormLayout()
        layout_mat.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        layout_mat.setVerticalSpacing(8)
        
        self.combo_concrete_material = QComboBox()
        self.combo_concrete_material.setEditable(True)
        self.combo_concrete_material.addItem("-- Sin conexión a SAP2000 --")
        self.combo_concrete_material.setToolTip("Material de hormigón (compartido para todas las secciones)")
        layout_mat.addRow("Hormigón:", self.combo_concrete_material)
        
        self.combo_rebar_material = QComboBox()
        self.combo_rebar_material.setEditable(True)
        self.combo_rebar_material.addItem("-- Sin conexión a SAP2000 --")
        self.combo_rebar_material.setToolTip("Material de acero para refuerzo")
        layout_mat.addRow("Acero Refuerzo:", self.combo_rebar_material)
        
        group_materiales.setLayout(layout_mat)
        layout_def.addWidget(group_materiales)
        
        # --- Pedestal ---
        group_pedestales = QGroupBox("Crear Sección de Pedestal (Section Designer)")
        layout_ped = QFormLayout()
        layout_ped.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        layout_ped.setVerticalSpacing(8)
        
        self.edit_section_name = QLineEdit("PED_01")
        self.edit_section_name.setMaximumWidth(150)
        layout_ped.addRow("Nombre:", self.edit_section_name)
        
        # Dimensiones en horizontal
        dims_layout = QHBoxLayout()
        self.edit_width = QLineEdit("500")
        self.edit_width.setMaximumWidth(80)
        dims_layout.addWidget(QLabel("Ancho (Y GLOBAL):"))
        dims_layout.addWidget(self.edit_width)
        dims_layout.addWidget(QLabel("mm"))
        dims_layout.addSpacing(15)
        self.edit_height = QLineEdit("500")
        self.edit_height.setMaximumWidth(80)
        dims_layout.addWidget(QLabel("Alto (X GLOBAL):"))
        dims_layout.addWidget(self.edit_height)
        dims_layout.addWidget(QLabel("mm"))
        dims_layout.addStretch()
        layout_ped.addRow("Dimensiones:", dims_layout)
        
        # Refuerzo
        self.combo_corner_bars = QComboBox()
        self.combo_corner_bars.setEditable(True)
        default_bars = ["12mm", "16mm", "20mm", "25mm", "32mm", "#6", "#8", "#10"]
        self.combo_corner_bars.addItems(default_bars)
        self.combo_corner_bars.setCurrentText("16mm")
        self.combo_corner_bars.setMaximumWidth(100)
        layout_ped.addRow("Barras Esquinas:", self.combo_corner_bars)
        
        self.combo_edge_bars = QComboBox()
        self.combo_edge_bars.setEditable(True)
        self.combo_edge_bars.addItems(default_bars)
        self.combo_edge_bars.setCurrentText("12mm")
        self.combo_edge_bars.setMaximumWidth(100)
        layout_ped.addRow("Barras Bordes:", self.combo_edge_bars)
        
        # Espaciamiento y recubrimiento en horizontal
        spacing_layout = QHBoxLayout()
        self.edit_spacing = QLineEdit("150")
        self.edit_spacing.setMaximumWidth(70)
        spacing_layout.addWidget(QLabel("Esp:"))
        spacing_layout.addWidget(self.edit_spacing)
        spacing_layout.addWidget(QLabel("mm"))
        spacing_layout.addSpacing(15)
        self.edit_cover = QLineEdit("30")
        self.edit_cover.setMaximumWidth(70)
        spacing_layout.addWidget(QLabel("Recub:"))
        spacing_layout.addWidget(self.edit_cover)
        spacing_layout.addWidget(QLabel("mm"))
        spacing_layout.addStretch()
        layout_ped.addRow("Refuerzo:", spacing_layout)
        
        self.btn_create_section = QPushButton("✨ Crear Sección Pedestal")
        self.btn_create_section.clicked.connect(self.create_pedestal_section)
        self.btn_create_section.setEnabled(False)
        self.btn_create_section.setStyleSheet("font-weight: bold; padding: 8px;")
        layout_ped.addRow("", self.btn_create_section)
        
        group_pedestales.setLayout(layout_ped)
        layout_def.addWidget(group_pedestales)
        
        # --- Zapata ---
        group_zapatas = QGroupBox("Crear Sección de Zapata (Shell-Thick)")
        layout_zap = QFormLayout()
        layout_zap.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        layout_zap.setVerticalSpacing(8)
        
        self.edit_zapata_name = QLineEdit("LOSA_")
        self.edit_zapata_name.setMaximumWidth(150)
        self.edit_zapata_name.setToolTip("Se crearán: LOSA_ (gris claro) y LOSA_PED (gris oscuro)")
        layout_zap.addRow("Nombre Base:", self.edit_zapata_name)
        
        self.edit_zapata_thickness = QLineEdit("300")
        self.edit_zapata_thickness.setMaximumWidth(100)
        layout_zap.addRow("Espesor (mm):", self.edit_zapata_thickness)
        
        self.btn_create_zapata = QPushButton("✨ Crear Secciones Shell")
        self.btn_create_zapata.clicked.connect(self.create_zapata_sections)
        self.btn_create_zapata.setEnabled(False)
        self.btn_create_zapata.setStyleSheet("font-weight: bold; padding: 8px;")
        layout_zap.addRow("", self.btn_create_zapata)
        
        info_label = QLabel("💡 Se crearán 2 secciones con colores diferentes")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 9pt;")
        layout_zap.addRow(info_label)
        
        group_zapatas.setLayout(layout_zap)
        layout_def.addWidget(group_zapatas)
        
        layout_def.addStretch()
        self.tab_widget.addTab(tab_definiciones, "📋 Definiciones")
        
        # ========== PESTAÑA 2: MODELAR ==========
        tab_modelar = QWidget()
        layout_mod = QVBoxLayout(tab_modelar)
        layout_mod.setSpacing(15)
        
        # --- Ubicación ---
        group_ubicacion = QGroupBox("📍 Ubicación")
        layout_ubic = QVBoxLayout()
        
        # Coordenadas en horizontal
        coords_layout = QHBoxLayout()
        coords_layout.addWidget(QLabel("Origen:"))
        
        self.edit_origen_x = QLineEdit("0.0")
        self.edit_origen_x.setMaximumWidth(80)
        coords_layout.addWidget(QLabel("X:"))
        coords_layout.addWidget(self.edit_origen_x)
        coords_layout.addWidget(QLabel("mm"))
        
        self.edit_origen_y = QLineEdit("0.0")
        self.edit_origen_y.setMaximumWidth(80)
        coords_layout.addWidget(QLabel("Y:"))
        coords_layout.addWidget(self.edit_origen_y)
        coords_layout.addWidget(QLabel("mm"))
        
        self.edit_origen_z = QLineEdit("0.0")
        self.edit_origen_z.setMaximumWidth(80)
        coords_layout.addWidget(QLabel("Z:"))
        coords_layout.addWidget(self.edit_origen_z)
        coords_layout.addWidget(QLabel("mm"))
        
        self.btn_get_coords = QPushButton("📍 Obtener de Nodo Seleccionado")
        self.btn_get_coords.clicked.connect(self.fetch_coords)
        self.btn_get_coords.setEnabled(False)
        coords_layout.addWidget(self.btn_get_coords)
        coords_layout.addStretch()
        
        layout_ubic.addLayout(coords_layout)
        group_ubicacion.setLayout(layout_ubic)
        layout_mod.addWidget(group_ubicacion)
        
        # --- Componentes ---
        group_componentes = QGroupBox("🏗️ Componentes de la Fundación")
        layout_comp = QFormLayout()
        layout_comp.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        layout_comp.setVerticalSpacing(10)
        
        # Sección Frame con botón de actualización
        frame_section_layout = QHBoxLayout()
        self.combo_seccion_frame = QComboBox()
        self.combo_seccion_frame.setEditable(True)
        self.combo_seccion_frame.addItem("-- Sin conexión a SAP2000 --")
        self.combo_seccion_frame.setToolTip("Sección para el elemento Frame (pedestal)")
        frame_section_layout.addWidget(self.combo_seccion_frame)
        
        self.btn_reload_frame = QPushButton("🔄")
        self.btn_reload_frame.setMaximumWidth(40)
        self.btn_reload_frame.setToolTip("Actualizar secciones de Frame disponibles")
        self.btn_reload_frame.clicked.connect(self.load_sections)
        self.btn_reload_frame.setEnabled(False)
        frame_section_layout.addWidget(self.btn_reload_frame)
        
        layout_comp.addRow("Sección Frame:", frame_section_layout)
        
        # Dimensiones Pedestal (horizontal)
        dims_ped_layout = QHBoxLayout()
        dims_ped_layout.addWidget(QLabel("Altura:"))
        self.edit_altura_pedestal = QLineEdit("1000")
        self.edit_altura_pedestal.setMaximumWidth(80)
        self.edit_altura_pedestal.setToolTip("Altura del elemento pedestal (distancia vertical del frame)")
        dims_ped_layout.addWidget(self.edit_altura_pedestal)
        dims_ped_layout.addWidget(QLabel("mm"))
        
        dims_ped_layout.addSpacing(15)
        dims_ped_layout.addWidget(QLabel("Ancho (X GLOBAL):"))
        self.edit_ancho_pedestal = QLineEdit("500")
        self.edit_ancho_pedestal.setMaximumWidth(80)
        self.edit_ancho_pedestal.setToolTip("Ancho de la sección del pedestal (dimensión X)")
        dims_ped_layout.addWidget(self.edit_ancho_pedestal)
        dims_ped_layout.addWidget(QLabel("mm"))
        
        dims_ped_layout.addSpacing(15)
        dims_ped_layout.addWidget(QLabel("Alto (Y GLOBAL):"))
        self.edit_alto_pedestal = QLineEdit("500")
        self.edit_alto_pedestal.setMaximumWidth(80)
        self.edit_alto_pedestal.setToolTip("Alto de la sección del pedestal (dimensión Y)")
        dims_ped_layout.addWidget(self.edit_alto_pedestal)
        dims_ped_layout.addWidget(QLabel("mm"))
        dims_ped_layout.addStretch()
        layout_comp.addRow("Dimensión Pedestal:", dims_ped_layout)
        
        # Sección Shell con botón de actualización
        shell_section_layout = QHBoxLayout()
        self.combo_seccion_shell = QComboBox()
        self.combo_seccion_shell.setEditable(True)
        self.combo_seccion_shell.addItem("-- Sin conexión a SAP2000 --")
        self.combo_seccion_shell.setToolTip("Sección Shell para la losa debajo del pedestal")
        shell_section_layout.addWidget(self.combo_seccion_shell)
        
        self.btn_reload_shell = QPushButton("🔄")
        self.btn_reload_shell.setMaximumWidth(40)
        self.btn_reload_shell.setToolTip("Actualizar secciones de Shell disponibles")
        self.btn_reload_shell.clicked.connect(self.load_sections)
        self.btn_reload_shell.setEnabled(False)
        shell_section_layout.addWidget(self.btn_reload_shell)
        
        layout_comp.addRow("Sección Zapata:", shell_section_layout)
        
        # Espesor Zapata
        self.edit_espesor_zapata = QLineEdit("300")
        self.edit_espesor_zapata.setMaximumWidth(100)
        self.edit_espesor_zapata.setToolTip("Espesor de la zapata (para cálculo de link)")
        layout_comp.addRow("Espesor Zapata (mm):", self.edit_espesor_zapata)
        
        group_componentes.setLayout(layout_comp)
        layout_mod.addWidget(group_componentes)
        
        # --- Opciones Avanzadas ---
        group_opciones = QGroupBox("⚙️ Opciones de Malla")
        layout_opc = QFormLayout()
        layout_opc.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        
        mesh_layout = QHBoxLayout()
        self.edit_mesh_nx = QLineEdit("4")
        self.edit_mesh_nx.setMaximumWidth(50)
        mesh_layout.addWidget(QLabel("Divisiones X:"))
        mesh_layout.addWidget(self.edit_mesh_nx)
        mesh_layout.addSpacing(15)
        self.edit_mesh_ny = QLineEdit("4")
        self.edit_mesh_ny.setMaximumWidth(50)
        mesh_layout.addWidget(QLabel("Y:"))
        mesh_layout.addWidget(self.edit_mesh_ny)
        mesh_layout.addStretch()
        layout_opc.addRow("Malla de Losa:", mesh_layout)
        
        group_opciones.setLayout(layout_opc)
        layout_mod.addWidget(group_opciones)
        
        # --- Botón Modelar ---
        self.btn_modelar_fundacion = QPushButton("🏗️ MODELAR FUNDACIÓN COMPLETA")
        self.btn_modelar_fundacion.clicked.connect(self.model_foundation)
        self.btn_modelar_fundacion.setEnabled(False)
        self.btn_modelar_fundacion.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                font-weight: bold;
                padding: 12px;
                background-color: #27ae60;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        layout_mod.addWidget(self.btn_modelar_fundacion)
        
        layout_mod.addStretch()
        self.tab_widget.addTab(tab_modelar, "🏗️ Modelar")
        
        main_layout.addWidget(self.tab_widget)
        
        # --- Log Area ---
        group_log = QGroupBox("Log de Operaciones")
        layout_log = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout_log.addWidget(self.log_text)
        
        group_log.setLayout(layout_log)
        main_layout.addWidget(group_log)
        
        self.log("Módulo de Fundaciones iniciado")
        self.log("💡 Pestaña 'Definiciones': Crear secciones | Pestaña 'Modelar': Crear fundación")
    
    def on_connection_changed(self, connected):
        """
        Se ejecuta cuando cambia el estado de conexión con SAP2000.
        
        Args:
            connected (bool): True si está conectado, False si no
        """
        self.btn_create_section.setEnabled(connected)
        self.btn_create_zapata.setEnabled(connected)
        self.btn_get_coords.setEnabled(connected)
        self.btn_modelar_fundacion.setEnabled(connected)
        self.btn_reload_frame.setEnabled(connected)
        self.btn_reload_shell.setEnabled(connected)
        
        if connected:
            self.log("✓ Conectado a SAP2000")
            # Cargar materiales y secciones automáticamente al conectar
            self.load_materials()
            self.load_sections()
        else:
            self.log("⚠️ Desconectado de SAP2000")
            self.combo_concrete_material.clear()
            self.combo_concrete_material.addItem("-- Sin conexión a SAP2000 --")
            self.combo_rebar_material.clear()
            self.combo_rebar_material.addItem("-- Sin conexión a SAP2000 --")
            
            # Resetear secciones
            self.combo_seccion_frame.clear()
            self.combo_seccion_frame.addItem("-- Sin conexión a SAP2000 --")
            self.combo_seccion_shell.clear()
            self.combo_seccion_shell.addItem("-- Sin conexión a SAP2000 --")
            
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
            
            # Limpiar combo
            self.combo_concrete_material.clear()
            
            if concrete_mats:
                # Agregar materiales
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
    
    def load_sections(self):
        """Carga las secciones de Frame y Shell desde el modelo SAP2000."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
            
            # --- Cargar secciones de Frame (hormigón) ---
            self.log("Obteniendo secciones de Frame del modelo...")
            frame_sections = self.backend.get_concrete_frame_sections()
            
            # Guardar selección actual
            current_frame = self.combo_seccion_frame.currentText()
            
            # Actualizar combo de Frame
            self.combo_seccion_frame.clear()
            
            if frame_sections:
                for sec_name in frame_sections:
                    self.combo_seccion_frame.addItem(sec_name)
                
                # Restaurar selección previa si existe
                idx = self.combo_seccion_frame.findText(current_frame)
                if idx >= 0:
                    self.combo_seccion_frame.setCurrentIndex(idx)
                else:
                    self.combo_seccion_frame.setCurrentIndex(0)
                
                self.log(f"✓ {len(frame_sections)} secciones de Frame encontradas")
            else:
                self.combo_seccion_frame.addItem("-- No hay secciones de Frame --")
                self.log("⚠️ No se encontraron secciones de Frame en el modelo")
            
            # --- Cargar secciones de Shell ---
            self.log("Obteniendo secciones de Shell del modelo...")
            shell_sections = self.backend.get_shell_sections()
            
            # Guardar selección actual
            current_shell = self.combo_seccion_shell.currentText()
            
            # Actualizar combo de Shell
            self.combo_seccion_shell.clear()
            
            if shell_sections:
                for sec_name in shell_sections:
                    self.combo_seccion_shell.addItem(sec_name)
                
                # Restaurar selección previa si existe
                idx = self.combo_seccion_shell.findText(current_shell)
                if idx >= 0:
                    self.combo_seccion_shell.setCurrentIndex(idx)
                else:
                    self.combo_seccion_shell.setCurrentIndex(0)
                
                self.log(f"✓ {len(shell_sections)} secciones de Shell encontradas")
            else:
                self.combo_seccion_shell.addItem("-- No hay secciones de Shell --")
                self.log("⚠️ No se encontraron secciones de Shell en el modelo")
                
        except Exception as e:
            self.log(f"❌ Error cargando secciones: {e}")
            import traceback
            traceback.print_exc()
    
    def fetch_coords(self):
        """Obtiene las coordenadas del punto seleccionado en SAP2000."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
            
            self.log("Obteniendo coordenadas de punto seleccionado...")
            coords = self.backend.get_selected_point_coords()
            
            if coords:
                self.edit_origen_x.setText(f"{coords['x']:.4f}")
                self.edit_origen_y.setText(f"{coords['y']:.4f}")
                self.edit_origen_z.setText(f"{coords['z']:.4f}")
                self.log(f"✓ Coordenadas actualizadas desde punto '{coords['name']}'")
            else:
                self.log("⚠️ No se encontró ningún punto seleccionado.")
                
        except Exception as e:
            self.log(f"❌ Error obteniendo coordenadas: {e}")
            import traceback
            traceback.print_exc()
    
    def create_zapata_sections(self):
        """Crea dos secciones Shell-Thick para losa de fundación."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
            
            # Obtener valores de los inputs
            base_name = self.edit_zapata_name.text().strip()
            material = self.combo_concrete_material.currentText().strip()
            
            # Validaciones
            if not base_name:
                self.log("❌ Debe especificar un nombre base para las secciones")
                return
            
            if "--" in material or not material:
                self.log("❌ Debe seleccionar un material de hormigón válido")
                return
            
            # Convertir espesor a float
            try:
                thickness = float(self.edit_zapata_thickness.text())
            except ValueError:
                self.log("❌ El espesor debe ser un valor numérico")
                return
            
            if thickness <= 0:
                self.log("❌ El espesor debe ser mayor a cero")
                return
            
            # Nombres de las secciones a crear
            section_name_1 = base_name
            section_name_2 = base_name + "PED"
            
            # Log de inicio
            self.log("=" * 60)
            self.log(f"Creando secciones Shell-Thick:")
            self.log(f"  Sección 1: {section_name_1} (gris claro)")
            self.log(f"  Sección 2: {section_name_2} (gris oscuro)")
            self.log(f"  Material: {material}")
            self.log(f"  Espesor: {thickness} mm")
            self.log("-" * 60)
            
            # Llamar al backend para crear las secciones
            success = self.backend.create_shell_thick_sections(
                base_name=base_name,
                material=material,
                thickness=thickness
            )
            
            if success:
                self.log("=" * 60)
                self.log(f"✅ Secciones creadas exitosamente!")
                self.log(f"   • {section_name_1}")
                self.log(f"   • {section_name_2}")
                self.log("=" * 60)
                
                # Incrementar nombre para próxima sección
                import re
                match = re.search(r'(\d+)$', base_name)
                if match:
                    num = int(match.group(1))
                    base_prefix = base_name[:match.start()]
                    next_name = f"{base_prefix}{num + 1:02d}"
                    self.edit_zapata_name.setText(next_name)
            else:
                self.log("❌ Error al crear las secciones. Revise el log para detalles")
                
        except Exception as e:
            self.log(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def model_foundation(self):
        """Modela la fundación: crea frame de pedestal y link rígido."""
        if not self.sap_interface or not self.sap_interface.SapModel:
            self.log("⚠️ No hay conexión con SAP2000")
            return
        
        try:
            # Crear backend si no existe
            if not self.backend:
                self.backend = FundacionesBackend(self.sap_interface.SapModel)
            
            # Obtener valores de los inputs
            try:
                x = float(self.edit_origen_x.text())
                y = float(self.edit_origen_y.text())
                z = float(self.edit_origen_z.text())
                altura_pedestal = float(self.edit_altura_pedestal.text())
                ancho_seccion = float(self.edit_ancho_pedestal.text())
                alto_seccion = float(self.edit_alto_pedestal.text())
                espesor_zapata = float(self.edit_espesor_zapata.text())
                mesh_nx = int(self.edit_mesh_nx.text())
                mesh_ny = int(self.edit_mesh_ny.text())
            except ValueError:
                self.log("❌ Las coordenadas, dimensiones, espesor y divisiones de malla deben ser valores numéricos")
                return
            
            # Obtener sección del frame y shell
            frame_section = self.combo_seccion_frame.currentText().strip()
            shell_section = self.combo_seccion_shell.currentText().strip()
            
            # Validaciones
            if "--" in frame_section or not frame_section:
                self.log("❌ Debe seleccionar una sección de Frame válida")
                return
            
            if "--" in shell_section or not shell_section:
                self.log("❌ Debe seleccionar una sección de Zapata válida")
                return
            
            if altura_pedestal <= 0:
                self.log("❌ La altura del pedestal debe ser mayor a cero")
                return
            
            if ancho_seccion <= 0 or alto_seccion <= 0:
                self.log("❌ Las dimensiones del pedestal deben ser mayores a cero")
                return
            
            if espesor_zapata <= 0:
                self.log("❌ El espesor de la zapata debe ser mayor a cero")
                return
            
            if mesh_nx <= 0 or mesh_ny <= 0:
                self.log("❌ Las divisiones de malla deben ser mayores a cero")
                return
            
            # Log de inicio
            self.log("=" * 60)
            self.log("🏗️ Modelando Fundación:")
            self.log(f"  Origen: ({x}, {y}, {z}) mm")
            self.log(f"  Altura Pedestal: {altura_pedestal} mm")
            self.log(f"  Dimensiones Pedestal: {ancho_seccion:.0f} x {alto_seccion:.0f} mm")
            self.log(f"  Espesor Zapata: {espesor_zapata} mm")
            self.log(f"  Malla Losa: {mesh_nx} x {mesh_ny}")
            self.log(f"  Sección Frame: {frame_section}")
            self.log(f"  Sección Shell: {shell_section}")
            self.log("-" * 60)
            
            # --- PASO 1: Crear Frame de Pedestal ---
            # Punto inicial: coordenadas ingresadas
            x1, y1, z1 = x, y, z
            # Punto final: restar altura del pedestal a Z
            x2, y2, z2 = x, y, z - altura_pedestal
            
            self.log(f"1️⃣ Creando Frame de Pedestal:")
            self.log(f"   Desde: ({x1}, {y1}, {z1})")
            self.log(f"   Hasta: ({x2}, {y2}, {z2})")
            
            frame_name, pt1_name, pt2_name = self.backend.create_frame_element(
                x1, y1, z1, x2, y2, z2, frame_section
            )
            
            if not frame_name:
                self.log("❌ Error al crear el frame. Revise el log para detalles")
                return
            
            self.log(f"   ✅ Frame creado: {frame_name}")
            self.log(f"   Puntos: {pt1_name} → {pt2_name}")
            
            # --- PASO 2: Crear Propiedad de Link Rígido ---
            self.log(f"2️⃣ Creando propiedad de link rígido:")
            
            link_prop_name = "LIN_RIGIDO"
            success = self.backend.create_rigid_link_property(link_prop_name)
            
            if not success:
                self.log("⚠️ Advertencia: No se pudo crear la propiedad (puede que ya exista)")
                # Continuar de todas formas, la propiedad puede ya existir
            else:
                self.log(f"   ✅ Propiedad creada: {link_prop_name}")
            
            # --- PASO 3: Crear Link Rígido ---
            # Punto inicial: donde terminó el frame (x2, y2, z2)
            x3, y3, z3 = x2, y2, z2
            # Punto final: mitad del espesor de zapata hacia abajo
            x4, y4, z4 = x2, y2, z2 - (espesor_zapata / 2.0)
            
            self.log(f"3️⃣ Creando Link Rígido:")
            self.log(f"   Desde: ({x3}, {y3}, {z3})")
            self.log(f"   Hasta: ({x4}, {y4}, {z4})")
            
            link_name, pt3_name, pt4_name = self.backend.create_link_element(
                x3, y3, z3, x4, y4, z4, link_prop_name
            )
            
            if not link_name:
                self.log("❌ Error al crear el link. Revise el log para detalles")
                return
            
            self.log(f"   ✅ Link creado: {link_name}")
            self.log(f"   Puntos: {pt3_name} → {pt4_name}")
            
            # --- PASO 4: Crear Losa Rectangular (debajo del pedestal) ---
            # La losa se crea en el plano XY, en la posición Z del punto final del link
            # Centrada en (x, y), con dimensiones ancho_seccion x alto_seccion
            # Dividida según mesh_nx x mesh_ny
            
            self.log(f"4️⃣ Creando Losa Rectangular (debajo del pedestal):")
            self.log(f"   Centro: ({x}, {y}), Z: {z4}")
            self.log(f"   Dimensiones: {ancho_seccion:.0f} x {alto_seccion:.0f} mm")
            self.log(f"   Malla: {mesh_nx} x {mesh_ny} elementos")
            self.log(f"   Sección: {shell_section}")
            
            created_areas = self.backend.create_rectangular_slab_mesh(
                center_x=x,
                center_y=y,
                z=z4,
                width=ancho_seccion,
                height=alto_seccion,
                shell_section=shell_section,
                nx=mesh_nx,
                ny=mesh_ny
            )
            
            if created_areas:
                self.log(f"   ✅ Losa creada: {len(created_areas)} elementos")
            else:
                self.log("   ⚠️ Advertencia: No se pudieron crear elementos de losa")
            
            # Resumen final
            self.log("=" * 60)
            self.log("🎉 ¡Fundación modelada exitosamente!")
            self.log(f"   • Frame: {frame_name} (sección: {frame_section})")
            self.log(f"   • Link: {link_name} (propiedad: {link_prop_name})")
            self.log(f"   • Losa: {len(created_areas)} elementos (sección: {shell_section})")
            self.log("=" * 60)
            
            if created_areas:
                self.log(f"   ✅ Losa creada: {len(created_areas)} elementos")
            else:
                self.log("   ⚠️ Advertencia: No se pudieron crear elementos de losa")
            
            # Resumen final
            self.log("=" * 60)
            self.log("🎉 ¡Fundación modelada exitosamente!")
            self.log(f"   • Frame: {frame_name} (sección: {frame_section})")
            self.log(f"   • Link: {link_name} (propiedad: {link_prop_name})")
            self.log(f"   • Losa: {len(created_areas)} elementos (sección: {shell_section})")
            self.log("=" * 60)
            
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
