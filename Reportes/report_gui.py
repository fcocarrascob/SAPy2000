from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QGroupBox, QGridLayout, QMessageBox, QComboBox, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt
from .report_backend import ReportBackend
from .template_engine import TemplateEngine
from .snippet_manager import SnippetManager
import os
import glob

class ReportWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.snippet_manager = SnippetManager()
        self.setup_ui()


    def setup_ui(self):
        # Layout principal vertical
        main_layout = QVBoxLayout(self)
        
        # --- Cabecera ---
        header_label = QLabel("Generador de Memorias")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        main_layout.addWidget(header_label)

        # --- Sección 1: Generación Automática (Templates) ---
        group_gen = QGroupBox("1. Generar Estructura Base")
        gen_layout = QVBoxLayout()
        
        hbox_template = QHBoxLayout()
        hbox_template.addWidget(QLabel("Template:"))
        self.combo_templates = QComboBox()
        hbox_template.addWidget(self.combo_templates)
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(30)
        btn_refresh.clicked.connect(self.load_templates)
        hbox_template.addWidget(btn_refresh)
        gen_layout.addLayout(hbox_template)

        btn_generate_tmpl = QPushButton("Generar Documento Nuevo")
        btn_generate_tmpl.setStyleSheet("background-color: #d0f0c0; font-weight: bold;")
        btn_generate_tmpl.clicked.connect(self.run_template_generation)
        gen_layout.addWidget(btn_generate_tmpl)

        group_gen.setLayout(gen_layout)
        main_layout.addWidget(group_gen)

        # --- Sección 2: Herramientas en Vivo (Live Assistant) ---
        group_live = QGroupBox("2. Datos desde SAP2000")
        live_layout = QGridLayout()
        
        btn_materials = QPushButton("Materiales")
        btn_materials.clicked.connect(lambda: self.run_action("insert_materials_table"))
        btn_sections = QPushButton("Secc. Frame")
        btn_sections.clicked.connect(lambda: self.run_action("insert_frame_sections"))
        btn_patterns = QPushButton("Patrones Carga")
        btn_patterns.clicked.connect(lambda: self.run_action("insert_load_patterns_table"))
        btn_combos = QPushButton("Combinaciones")
        btn_combos.clicked.connect(lambda: self.run_action("insert_load_combinations_table"))

        live_layout.addWidget(btn_materials, 0, 0)
        live_layout.addWidget(btn_sections, 0, 1)
        live_layout.addWidget(btn_patterns, 1, 0)
        live_layout.addWidget(btn_combos, 1, 1)
        
        group_live.setLayout(live_layout)
        main_layout.addWidget(group_live)
        
        # --- Sección 3: Librería de Contenido ---
        group_lib = QGroupBox("3. Librería de Contenido")
        lib_vbox = QVBoxLayout()
        
        # Selector de Categoria
        hbox_cat = QHBoxLayout()
        hbox_cat.addWidget(QLabel("Categoría:"))
        self.combo_categories = QComboBox()
        self.combo_categories.currentIndexChanged.connect(self.on_category_changed)
        hbox_cat.addWidget(self.combo_categories)
        lib_vbox.addLayout(hbox_cat)
        
        # Lista de Snippets
        self.list_snippets = QListWidget()
        self.list_snippets.itemClicked.connect(self.on_snippet_selected)
        # Limitar altura para que no ocupe toda la pantalla
        self.list_snippets.setMaximumHeight(150)
        lib_vbox.addWidget(self.list_snippets)
        
        # Preview rápido (Titulo/Desc)
        self.lbl_preview = QLabel("Seleccione un elemento para ver descripción...")
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setStyleSheet("color: gray; font-style: italic; margin: 5px;")
        self.lbl_preview.setMaximumHeight(60)
        lib_vbox.addWidget(self.lbl_preview)
        
        # Botones de libreria
        hbox_lib_btns = QHBoxLayout()
        
        self.btn_insert_snippet = QPushButton("Insertar en Cursor")
        self.btn_insert_snippet.setEnabled(False)
        self.btn_insert_snippet.clicked.connect(self.insert_current_snippet)
        
        btn_reload_lib = QPushButton("Recargar Lib.")
        btn_reload_lib.clicked.connect(self.reload_library)
        
        hbox_lib_btns.addWidget(self.btn_insert_snippet)
        hbox_lib_btns.addWidget(btn_reload_lib)
        
        lib_vbox.addLayout(hbox_lib_btns)
        
        group_lib.setLayout(lib_vbox)
        main_layout.addWidget(group_lib)
        
        main_layout.addStretch()

        # Cargar datos iniciales
        self.load_templates()
        self.reload_library()


    def load_templates(self):
        """Busca archivos .json en la carpeta templates."""
        self.combo_templates.clear()
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            
        files = glob.glob(os.path.join(self.templates_dir, "*.json"))
        for f in files:
            name = os.path.basename(f)
            self.combo_templates.addItem(name, f)

    def reload_library(self):
        """Recarga la librería de snippets."""
        self.snippet_manager.load_library()
        cats = self.snippet_manager.get_categories()
        self.combo_categories.clear()
        self.combo_categories.addItems(cats)
        if cats:
            self.on_category_changed()
        else:
            self.list_snippets.clear()

    def on_category_changed(self):
        """Actualiza la lista al cambiar categoría."""
        cat = self.combo_categories.currentText()
        items = self.snippet_manager.get_snippets_in_category(cat)
        self.list_snippets.clear()
        
        for item in items:
            list_item = QListWidgetItem(item.get("title", "Sin Título"))
            # Guardamos el objeto entero en data (role user)
            list_item.setData(Qt.UserRole, item)
            self.list_snippets.addItem(list_item)
            
        self.lbl_preview.setText("")
        self.btn_insert_snippet.setEnabled(False)

    def on_snippet_selected(self, item):
        data = item.data(Qt.UserRole)
        desc = data.get("description", "")
        self.lbl_preview.setText(desc)
        self.btn_insert_snippet.setEnabled(True)

    def insert_current_snippet(self):
        item = self.list_snippets.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        blocks = data.get("content", [])
        
        if not blocks: return
        
        # Usamos el TemplateEngine (o WordService directo) para procesar bloques
        # Como TemplateEngine.process_blocks es lo que queremos, instanciamos uno temporal
        engine = TemplateEngine()
        # Aseguramos conexión WordService dentro de engine
        engine.word_service.connect() 
        
        success = engine.process_blocks(blocks)
        if not success:
             QMessageBox.warning(self, "Error", "Error al insertar snippet.")

    def run_template_generation(self):
        template_path = self.combo_templates.currentData()
        if not template_path:
            QMessageBox.warning(self, "Aviso", "Seleccione un template válido.")
            return
            
        engine = TemplateEngine()
        success = engine.generate_structure(template_path)
        
        if success:
            QMessageBox.information(self, "Éxito", "Documento base generado correctamente.")
        else:
            QMessageBox.critical(self, "Error", "No se pudo generar el documento. Revise el log.")

    def run_action(self, method_name):

        """Ejecuta una acción del backend."""
        if not self.sap_interface:
            QMessageBox.critical(self, "Error", "Interfaz SAP no inicializada.")
            return

        model = self.sap_interface.SapModel
        if model is None:
            QMessageBox.warning(self, "Desconectado", "No hay conexión activa con SAP2000.")
            return

        try:
            backend = ReportBackend(model)
            method = getattr(backend, method_name)
            success = method()
            
            if success:
                # Opcional: Mostrar popup pequeño o solo log
                pass
            else:
                # Si falló (ej: tabla vacia), el backend ya logueó el error, 
                # pero podríamos avisar al usuario si devolvió False explícito.
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Error de Ejecución", f"Ocurrió un error al ejecutar la acción:\n{str(e)}")
