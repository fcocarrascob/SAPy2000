"""
Editor visual de Snippets para la Librería de Contenido.
Permite editar bloques de contenido con preview de ecuaciones en tiempo real.

NOTA: El preview de ecuaciones usa Word COM para renderizar UnicodeMath
de forma nativa, garantizando fidelidad con el resultado final.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QLabel,
    QGroupBox, QSpinBox, QStackedWidget, QWidget,
    QMessageBox, QDialogButtonBox, QToolButton, QMenu,
    QWidgetAction, QGridLayout, QScrollArea, QFrame,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QObject
from PySide6.QtGui import QAction
import logging
import tempfile
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QLabel,
    QGroupBox, QSpinBox, QStackedWidget, QWidget,
    QMessageBox, QDialogButtonBox, QToolButton, QMenu,
    QWidgetAction, QGridLayout, QScrollArea, QFrame,
    QApplication, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog
)

logger = logging.getLogger(__name__)

# Importar builder de ecuaciones UnicodeMath
from .equation_translator import (
    builder, validate_equation, get_symbols, get_templates, get_help
)


class EquationRibbon(QTabWidget):
    """
    Barra de herramientas estilo Ribbon para insertar estructuras UnicodeMath.
    """
    snippetClicked = Signal(str)  # Señal emitida al insertar un snippet (insert_text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)  # Altura fija para el ribbon
        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; background: #f0f0f0; }
            QTabBar::tab { background: #e0e0e0; padding: 4px 8px; border: 1px solid #ccc; border-bottom: none; }
            QTabBar::tab:selected { background: #fff; border-bottom: 1px solid #fff; }
        """)
        self.setup_tabs()

    def setup_tabs(self):
        # --- Estructuras ---
        struct_tab = QWidget()
        struct_layout = QHBoxLayout(struct_tab)
        struct_layout.setContentsMargins(4, 4, 4, 4)
        
        blocks = [
            ("Fracción", "(⬚)/(⬚)", "½"),
            ("Índice", "⬚^⬚", "x²"),
            ("Subíndice", "⬚_⬚", "x₂"),
            ("Raíz", "√(⬚)", "√"),
            ("Raíz N", "√(⬚&⬚)", "ⁿ√"),
            ("Paréntesis", "(⬚)", "( )"),
            ("Corchetes", "[⬚]", "[ ]"),
            ("Llaves", "{⬚}", "{ }"),
            ("Valor Abs.", "|⬚|", "|x|"),
        ]
        self._add_group(struct_layout, blocks)
        self.addTab(struct_tab, "Estructuras")

        # --- Cálculo/Op ---
        calc_tab = QWidget()
        calc_layout = QHBoxLayout(calc_tab)
        calc_layout.setContentsMargins(4, 4, 4, 4)

        calc_blocks = [
            ("Sumatoria", "∑_(⬚)^⬚ ⬚", "∑"),
            ("Integral", "∫_(⬚)^⬚ ⬚ d⬚", "∫"),
            ("Productoria", "∏_(⬚)^⬚ ⬚", "∏"),
            ("Límite", "lim_(⬚→⬚) ⬚", "lim"),
            ("Intersección", "∩", "∩"),
            ("Unión", "∪", "∪"),
        ]
        self._add_group(calc_layout, calc_blocks)
        self.addTab(calc_tab, "Cálculo")

        # --- Operadores ---
        ops_tab = QWidget()
        ops_layout = QGridLayout(ops_tab)
        ops_layout.setContentsMargins(4, 4, 4, 4)
        ops_layout.setSpacing(2)
        
        operators = [
            ("Igual", "="), ("Distinto", "≠"), ("Aprox", "≈"), ("Equiv", "≡"),
            ("Mayor", ">"), ("Menor", "<"), ("MayorEq", "≥"), ("MenorEq", "≤"),
            ("Mucho >", "≫"), ("Mucho <", "≪"), ("Prop", "∝"), ("MasMenos", "±"),
            ("Por", "×"), ("Div", "÷"), ("Punto", "⋅"), ("Círculo", "∘"),
            ("Flecha", "→"), ("Implica", "⇒"), ("DobleFlecha", "↔"), ("SiSoloSi", "⇔"),
            ("ParaTodo", "∀"), ("Existe", "∃"), ("Pertenece", "∈"), ("NoPertenece", "∉"),
            ("Infinito", "∞"), ("Nabla", "∇"), ("Parcial", "∂"), ("Grado", "°")
        ]
        
        row, col = 0, 0
        for name, char in operators:
            btn = QPushButton(char)
            btn.setFixedSize(40, 30)
            btn.setToolTip(name)
            btn.clicked.connect(lambda c=False, s=char: self.snippetClicked.emit(s))
            ops_layout.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1
        
        ops_layout.setRowStretch(row+1, 1)
        ops_layout.setColumnStretch(col+1, 1)
        self.addTab(ops_tab, "Operadores")

        # --- Matrices ---
        matrix_tab = QWidget()
        matrix_layout = QHBoxLayout(matrix_tab)
        matrix_layout.setContentsMargins(4, 4, 4, 4)

        matrix_blocks = [
            ("Matriz 2x2", "\\matrix(⬚&⬚@⬚&⬚)", "▦ 2x2"),
            ("Matriz 3x3", "\\matrix(⬚&⬚&⬚@⬚&⬚&⬚@⬚&⬚&⬚)", "▦ 3x3"),
            ("Vector Col", "\\matrix(⬚@⬚)", "日"),
            ("Vector Fila", "\\matrix(⬚&⬚)", "▭"),
            ("Cases", "❴█(⬚&if ⬚@⬚&if ⬚)", "{ Cases"),
            ("EqArray", "█(⬚&=⬚@⬚&=⬚)", "EqArray"),
            ("Matriz ( )", "(\\matrix(⬚&⬚@⬚&⬚))", "(▦)"),
            ("Matriz [ ]", "[\\matrix(⬚&⬚@⬚&⬚)]", "[▦]"),
        ]
        self._add_group(matrix_layout, matrix_blocks)
        self.addTab(matrix_tab, "Matrices")

        # --- Símbolos (Griegas) ---
        greek_tab = QWidget()
        greek_layout = QGridLayout(greek_tab) # Use Grid for many symbols
        greek_layout.setContentsMargins(4, 4, 4, 4)
        greek_layout.setSpacing(2)
        
        greeks = [
            ("alpha", "α"), ("beta", "β"), ("gamma", "γ"), ("theta", "θ"),
            ("lambda", "λ"), ("mu", "μ"), ("pi", "π"), ("sigma", "σ"),
            ("tau", "τ"), ("phi", "φ"), ("omega", "ω"), ("Delta", "Δ"),
            ("Sigma", "Σ"), ("Omega", "Ω"), ("epsilon", "ε"), ("rho", "ρ")
        ]
        
        row, col = 0, 0
        for name, char in greeks:
            btn = QPushButton(char)
            btn.setFixedSize(30, 30)
            btn.setToolTip(name)
            btn.clicked.connect(lambda c=False, s=char: self.snippetClicked.emit(s))
            greek_layout.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1
        
        # Add a stretch to push valid items to top-left
        greek_layout.setRowStretch(row+1, 1)
        greek_layout.setColumnStretch(col+1, 1)
        
        self.addTab(greek_tab, "Símbolos")


    def _add_group(self, layout, items):
        """Helper para agregar botones al layout"""
        for label, snippet, icon_text in items:
            btn = QPushButton(icon_text + "\n" + label)
            btn.setFixedSize(60, 60)
            btn.setToolTip(label)
            # Use style sheet to wrap text and center
            btn.setStyleSheet("text-align: center; padding: 2px;")
            
            # Conexión
            btn.clicked.connect(lambda c=False, s=snippet: self.snippetClicked.emit(s))
            layout.addWidget(btn)
        layout.addStretch()

class SymbolsPalette(QWidget):
    """Panel de símbolos LaTeX para insertar en ecuaciones."""
    
    symbolClicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        symbols = get_symbols()
        
        for category, syms in symbols.items():
            # Etiqueta de categoría
            lbl = QLabel(category)
            lbl.setStyleSheet("font-size: 10px; color: #666; margin-top: 4px;")
            layout.addWidget(lbl)
            
            # Grid de botones
            grid = QGridLayout()
            grid.setSpacing(1)
            
            col = 0
            row = 0
            max_cols = 5 if category == "Estructuras" else 6
            
            for latex_cmd, display in syms.items():
                # Mostrar el símbolo Unicode como texto del botón, insertar comando LaTeX
                if latex_cmd.startswith("\\"):
                    btn_text = display if len(display) == 1 else latex_cmd.replace("\\", "")[:6]
                else:
                    btn_text = latex_cmd[:6]
                
                btn = QPushButton(btn_text)
                btn.setMinimumWidth(40)
                btn.setFixedHeight(26)
                btn.setToolTip(f"{latex_cmd} → {display}")
                btn.setStyleSheet("font-size: 11px;")
                btn.clicked.connect(lambda checked, s=latex_cmd: self.symbolClicked.emit(s))
                grid.addWidget(btn, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            layout.addLayout(grid)
        
        layout.addStretch()


class UnicodeMathCheatsheet(QDialog):
    """
    Panel de ayuda interactivo con sintaxis UnicodeMath.
    
    Muestra ejemplos organizados por categoría que el usuario
    puede copiar directamente al portapapeles.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guía Rápida UnicodeMath")
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Sintaxis UnicodeMath para Word")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Área scrollable con ejemplos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # Categorías de ejemplos
        examples = {
            "Fracciones": [
                ("(a)/(b)", "Fracción simple"),
                ("(a+b)/(c+d)", "Fracción con expresiones"),
                ("(1)/(2)+(3)/(4)", "Suma de fracciones"),
            ],
            "Raíces": [
                ("√(x)", "Raíz cuadrada"),
                ("√(a^2+b^2)", "Raíz de expresión"),
                ("∛(x)", "Raíz cúbica"),
                ("∜(x)", "Raíz cuarta"),
                ("√(n&x)", "Raíz n-ésima (n&expresión)"),
            ],
            "Subíndices y Superíndices": [
                ("x_i", "Subíndice simple"),
                ("x_(ij)", "Subíndice compuesto"),
                ("x^2", "Superíndice simple"),
                ("x^(n+1)", "Superíndice compuesto"),
                ("x_i^2", "Ambos"),
                ("a_1^b_2", "Múltiples niveles"),
            ],
            "Matrices": [
                (r"\matrix(a&b@c&d)", "Matriz 2x2 (& columnas, @ filas)"),
                (r"(\matrix(a&b@c&d))", "Matriz con paréntesis"),
                (r"[\matrix(a&b@c&d)]", "Matriz con corchetes"),
                (r"\matrix(1&0&0@0&1&0@0&0&1)", "Matriz identidad 3x3"),
            ],
            "Ecuaciones Alineadas (eqarray)": [
                ("█(x+1&=2@y&=3)", "Sistema de ecuaciones"),
                ("█(x+1&=2@1+2+3+y&=z@(3)/(x)&=6)", "Sistema con fracción"),
            ],
            "Cases (Funciones por partes)": [
                ("f(x)=❴█(0&x<0@x&x≥0)", "Función con 2 casos"),
                ("|x|=❴█(x&x≥0@-x&x<0)", "Valor absoluto"),
            ],
            "Operadores N-arios": [
                ("∑_(i=1)^n x_i", "Sumatoria"),
                ("∏_(i=1)^n x_i", "Productoria"),
                ("∫_a^b f(x)dx", "Integral definida"),
                ("∬_D f(x,y)dA", "Integral doble"),
                ("∮_C F⋅dr", "Integral de línea"),
            ],
            "Límites": [
                ("lim_(n→∞) a_n", "Límite al infinito"),
                ("lim_(x→0) (sin x)/(x)", "Límite con fracción"),
            ],
            "Vectores y Acentos": [
                ("v⃗", "Vector (usar ⃗ después de letra)"),
                ("û", "Vector unitario"),
                ("x̄", "Barra sobre (promedio)"),
            ],
            "Texto en Ecuaciones": [
                ('"si "x>0', "Texto literal entre comillas"),
                ('a " donde " b', "Texto en medio"),
            ],
            "Símbolos Comunes": [
                ("α β γ δ ε θ λ μ π σ φ ω", "Griegas minúsculas"),
                ("Γ Δ Θ Λ Σ Φ Ω", "Griegas mayúsculas"),
                ("≠ ≥ ≤ ≈ ± × ÷ ⋅ ∞ → ⇒", "Operadores"),
            ],
            "Fórmulas Enmarcadas": [
                ("▭((a)/(b))", "Fórmula en recuadro"),
            ],
        }
        
        for category, items in examples.items():
            # Título de categoría
            cat_label = QLabel(category)
            cat_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333; margin-top: 5px;")
            content_layout.addWidget(cat_label)
            
            # Grid de ejemplos
            grid = QGridLayout()
            grid.setColumnStretch(0, 2)
            grid.setColumnStretch(1, 3)
            grid.setSpacing(4)
            
            for row, (code, desc) in enumerate(items):
                # Código copiable
                code_btn = QPushButton(code)
                code_btn.setStyleSheet("""
                    QPushButton {
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12px;
                        text-align: left;
                        padding: 4px 8px;
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #e8e8e8;
                        border-color: #999;
                    }
                """)
                code_btn.setToolTip("Click para copiar al portapapeles")
                code_btn.clicked.connect(lambda checked, c=code: self._copy_to_clipboard(c))
                grid.addWidget(code_btn, row, 0)
                
                # Descripción
                desc_label = QLabel(desc)
                desc_label.setStyleSheet("font-size: 11px; color: #666;")
                grid.addWidget(desc_label, row, 1)
            
            content_layout.addLayout(grid)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Nota al pie
        note = QLabel("💡 Tip: Escribe \\alpha, \\beta, etc. y se convertirán automáticamente a símbolos Unicode")
        note.setStyleSheet("font-size: 11px; color: #666; font-style: italic; margin-top: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        # Botón cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
    
    def _copy_to_clipboard(self, text):
        """Copia texto al portapapeles y muestra feedback."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # Feedback visual breve (tooltip)
        QMessageBox.information(self, "Copiado", f"'{text}' copiado al portapapeles")


class TemplatesMenu(QMenu):
    """Menú de templates de ecuaciones predefinidas."""
    
    templateSelected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("Templates", parent)
        self._build_menu()
    
    def _build_menu(self):
        templates = get_templates()
        
        for name, data in templates.items():
            action = self.addAction(name)
            action.setToolTip(data.get("description", ""))
            code = data.get("code", "")
            action.triggered.connect(lambda checked, c=code: self.templateSelected.emit(c))


class BlockEditor(QWidget):
    """Editor de un bloque individual con controles específicos por tipo."""
    
    contentChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._validate_equation)
        self.setup_ui()
        self._block_data = {}
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Selector de tipo
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["heading", "text", "equation", "table"])
        self.combo_type.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.combo_type)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # Stack de editores específicos por tipo
        self.editor_stack = QStackedWidget()
        
        # Editor para heading
        self.heading_editor = QWidget()
        h_layout = QVBoxLayout(self.heading_editor)
        h_form = QFormLayout()
        self.heading_content = QLineEdit()
        self.heading_content.textChanged.connect(lambda: self.contentChanged.emit())
        self.heading_level = QSpinBox()
        self.heading_level.setRange(1, 6)
        self.heading_level.setValue(3)
        h_form.addRow("Texto:", self.heading_content)
        h_form.addRow("Nivel:", self.heading_level)
        h_layout.addLayout(h_form)
        h_layout.addStretch()
        self.editor_stack.addWidget(self.heading_editor)
        
        # Editor para text
        self.text_editor = QWidget()
        t_layout = QVBoxLayout(self.text_editor)
        t_layout.addWidget(QLabel("Contenido:"))
        self.text_content = QTextEdit()
        self.text_content.textChanged.connect(self.contentChanged.emit)
        self.text_content.setMaximumHeight(100)
        t_layout.addWidget(self.text_content)
        
        # Tip para inline equations
        lbl_tip = QLabel("💡 Tip: Puedes insertar ecuaciones en línea usando signos $ (ej: $x=1$).")
        lbl_tip.setStyleSheet("font-size: 11px; color: #666; font-style: italic;")
        t_layout.addWidget(lbl_tip)
        
        t_layout.addStretch()
        self.editor_stack.addWidget(self.text_editor)
        
        # Editor para equation con preview y herramientas
        self.equation_editor = QWidget()
        e_layout = QVBoxLayout(self.equation_editor)
        e_layout.setContentsMargins(0,0,0,0)
        
        # Ribbon de Ecuaciones (Reemplaza toolbar anterior)
        self.ribbon = EquationRibbon()
        self.ribbon.snippetClicked.connect(self._insert_from_ribbon)
        e_layout.addWidget(self.ribbon)
        
        # Toolbar Auxiliar (Templates y Ayuda) - Debajo del Ribbon, más discreto
        aux_toolbar = QHBoxLayout()
        aux_toolbar.setContentsMargins(5, 0, 5, 0)
        
        # Botón de templates (Conserva funcionalidad original)
        self.btn_templates = QToolButton()
        self.btn_templates.setText("📚 Templates Estructurales")
        self.templates_menu = TemplatesMenu(self)
        self.templates_menu.templateSelected.connect(self._insert_template)
        self.btn_templates.setMenu(self.templates_menu)
        self.btn_templates.setPopupMode(QToolButton.InstantPopup)
        aux_toolbar.addWidget(self.btn_templates)
        
        aux_toolbar.addStretch()
        
        # Botón de ayuda UnicodeMath
        self.btn_help = QToolButton()
        self.btn_help.setText("? Guía de Sintaxis")
        self.btn_help.setToolTip("Abrir guía de sintaxis UnicodeMath")
        self.btn_help.clicked.connect(self._show_unicodemath_help)
        aux_toolbar.addWidget(self.btn_help)
        
        e_layout.addLayout(aux_toolbar)
        
        # Campo de ecuación
        self.equation_content = QTextEdit()
        self.equation_content.setMaximumHeight(80)
        self.equation_content.setPlaceholderText("Escribe la ecuación aquí o usa el Ribbon superior...")
        self.equation_content.textChanged.connect(self._on_equation_changed)
        e_layout.addWidget(self.equation_content)
        
        # Estado de validación
        self.lbl_validation = QLabel("")
        self.lbl_validation.setStyleSheet("font-size: 11px;")
        self.lbl_validation.setWordWrap(True)
        e_layout.addWidget(self.lbl_validation)
        
        e_layout.addStretch()
        self.editor_stack.addWidget(self.equation_editor)

        # Editor para Tabla
        self.table_editor = QWidget()
        self._setup_table_editor(self.table_editor)
        self.editor_stack.addWidget(self.table_editor)
        
        layout.addWidget(self.editor_stack)

    def _setup_table_editor(self, container):
        """Configura el editor de tablas."""
        layout = QVBoxLayout(container)
        
        # Toolbar de tabla
        toolbar = QHBoxLayout()
        
        btn_add_row = QPushButton("+ Fila")
        btn_add_row.clicked.connect(self._add_table_row)
        btn_del_row = QPushButton("- Fila")
        btn_del_row.clicked.connect(self._del_table_row)
        
        btn_add_col = QPushButton("+ Col")
        btn_add_col.clicked.connect(self._add_table_col)
        btn_del_col = QPushButton("- Col")
        btn_del_col.clicked.connect(self._del_table_col)
        
        toolbar.addWidget(btn_add_row)
        toolbar.addWidget(btn_del_row)
        toolbar.addSpacing(20)
        toolbar.addWidget(btn_add_col)
        toolbar.addWidget(btn_del_col)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Tabla
        self.table_widget = QTableWidget(2, 2)
        self.table_widget.setHorizontalHeaderLabels(["Header 1", "Header 2"])
        self.table_widget.setItem(0, 0, QTableWidgetItem("Cell 1"))
        self.table_widget.setItem(0, 1, QTableWidgetItem("Cell 2"))
        self.table_widget.setItem(1, 0, QTableWidgetItem("Cell 3"))
        self.table_widget.setItem(1, 1, QTableWidgetItem("Cell 4"))

        # Conectar cambios
        self.table_widget.itemChanged.connect(lambda: self.contentChanged.emit())
        
        # Haremos los headers editables via doble click
        self.table_widget.horizontalHeader().sectionDoubleClicked.connect(self._edit_header)
        
        layout.addWidget(self.table_widget)
        
        lbl_hint = QLabel("💡 Doble clic en encabezados para editar nombres.")
        lbl_hint.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(lbl_hint)

    def _edit_header(self, index):
        """Edita el texto de un encabezado."""
        header_item = self.table_widget.horizontalHeaderItem(index)
        current_text = header_item.text() if header_item else f"Header {index+1}"
        new_text, ok = QInputDialog.getText(self, "Editar Encabezado", "Nuevo nombre:", text=current_text)
        if ok:
            if not header_item:
                self.table_widget.setHorizontalHeaderItem(index, QTableWidgetItem(new_text))
            else:
                header_item.setText(new_text)
            self.contentChanged.emit()

    def _add_table_row(self):
        self.table_widget.insertRow(self.table_widget.rowCount())
        self.contentChanged.emit()

    def _del_table_row(self):
        if self.table_widget.rowCount() > 0:
            self.table_widget.removeRow(self.table_widget.rowCount() - 1)
            self.contentChanged.emit()

    def _add_table_col(self):
        col_idx = self.table_widget.columnCount()
        self.table_widget.insertColumn(col_idx)
        self.table_widget.setHorizontalHeaderItem(col_idx, QTableWidgetItem(f"Header {col_idx+1}"))
        self.contentChanged.emit()

    def _del_table_col(self):
        if self.table_widget.columnCount() > 0:
            self.table_widget.removeColumn(self.table_widget.columnCount() - 1)
            self.contentChanged.emit()
    
    def _insert_from_ribbon(self, snippet_text):
        """Inserta texto desde el ribbon y selecciona el primer placeholder."""
        cursor = self.equation_content.textCursor()
        cursor.insertText(snippet_text)
        
        # Buscar el placeholder ⬚
        # Intentamos retroceder para encontrar el primero insertado si hay varios
        # Pero simplificamos seleccionando el primero encontrado en el texto recién insertado ? 
        # Actually, simpler: just find "⬚" from current position backwards?
        # Better: find the first ⬚ inside the editor text to help user flow?
        # Or just simply set focus back.
        
        self.equation_content.setFocus()
        
        # Auto-seleccionar el primer placeholder "⬚" para facilitar edición
        # Obtenemos todo el texto
        full_text = self.equation_content.toPlainText()
        idx = full_text.find("⬚")
        if idx != -1:
            cursor.setPosition(idx)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, 1)
            self.equation_content.setTextCursor(cursor)

    def _setup_symbols_menu(self):
        """Configura el menú desplegable de símbolos. (DEPRECATED: Usado por el antiguo btn_symbols)"""
        # (Se mantiene si fuera necesario, pero ya no se llama desde _init_gui)
        pass
    
    def _insert_symbol(self, symbol):
        """Inserta un símbolo en la posición del cursor."""
        cursor = self.equation_content.textCursor()
        cursor.insertText(symbol)
        self.equation_content.setFocus()
    
    def _insert_template(self, template_code):
        """Inserta un template de ecuación."""
        self.equation_content.setPlainText(template_code)
        self.equation_content.setFocus()
    
    def _show_unicodemath_help(self):
        """Muestra el diálogo de ayuda UnicodeMath."""
        dialog = UnicodeMathCheatsheet(self)
        dialog.exec()
    
    def _on_type_changed(self, block_type):
        """Cambia el editor visible según el tipo."""
        idx = {"heading": 0, "text": 1, "equation": 2, "table": 3}.get(block_type, 1)
        self.editor_stack.setCurrentIndex(idx)
        self.contentChanged.emit()
    
    def _on_equation_changed(self):
        """Actualiza el editor de ecuación."""
        # Programar validación con delay (evitar validar cada keystroke)
        self._validation_timer.start(500)
        
        self.contentChanged.emit()
    
    def _validate_equation(self):
        """Valida la ecuación actual y muestra el resultado."""
        eq_text = self.equation_content.toPlainText()
        
        if not eq_text.strip():
            self.lbl_validation.setText("")
            return
        
        is_valid, error_msg = validate_equation(eq_text)
        
        if is_valid:
            self.lbl_validation.setText("✓ Sintaxis válida")
            self.lbl_validation.setStyleSheet("font-size: 11px; color: green;")
        else:
            self.lbl_validation.setText(f"⚠ {error_msg}")
            self.lbl_validation.setStyleSheet("font-size: 11px; color: #c00;")
    
    def set_block(self, block_data):
        """Carga un bloque en el editor."""
        self._block_data = block_data
        block_type = block_data.get("type", "text")
        content = block_data.get("content", "")
        params = block_data.get("parameters", {})
        
        # Bloquear señales temporalmente
        self.combo_type.blockSignals(True)
        self.equation_content.blockSignals(True)
        self.text_content.blockSignals(True)
        self.heading_content.blockSignals(True)
        self.table_widget.blockSignals(True)
        
        if block_type == "heading":
            self.combo_type.setCurrentText("heading")
            self.heading_content.setText(content)
            self.heading_level.setValue(params.get("level", 3))
            self.editor_stack.setCurrentIndex(0)
        elif block_type == "equation":
            self.combo_type.setCurrentText("equation")
            self.equation_content.setPlainText(content)
            self.editor_stack.setCurrentIndex(2)
        elif block_type == "table":
            self.combo_type.setCurrentText("table")
            self.editor_stack.setCurrentIndex(3)
            # Cargar tabla
            if isinstance(content, dict):
                headers = content.get("headers", [])
                data = content.get("data", [])
                
                self.table_widget.setColumnCount(len(headers))
                self.table_widget.setHorizontalHeaderLabels(headers)
                
                self.table_widget.setRowCount(len(data))
                for r, row_data in enumerate(data):
                    for c, cell_val in enumerate(row_data):
                        if c < self.table_widget.columnCount():
                            self.table_widget.setItem(r, c, QTableWidgetItem(str(cell_val)))
            else:
                # Default empty table
                self.table_widget.setRowCount(2)
                self.table_widget.setColumnCount(2)
                self.table_widget.setHorizontalHeaderLabels(["Header 1", "Header 2"])
                self.table_widget.setItem(0, 0, QTableWidgetItem(""))
        else:  # text y otros
            self.combo_type.setCurrentText("text")
            self.text_content.setPlainText(content if isinstance(content, str) else "")
            self.editor_stack.setCurrentIndex(1)
        
        # Desbloquear señales
        self.combo_type.blockSignals(False)
        self.equation_content.blockSignals(False)
        self.text_content.blockSignals(False)
        self.heading_content.blockSignals(False)
        self.table_widget.blockSignals(False)
    
    def get_block(self):
        """Retorna el bloque editado como diccionario."""
        block_type = self.combo_type.currentText()
        
        if block_type == "heading":
            return {
                "type": "heading",
                "content": self.heading_content.text(),
                "parameters": {"level": self.heading_level.value()}
            }
        elif block_type == "equation":
            return {
                "type": "equation",
                "content": self.equation_content.toPlainText(),
                "parameters": {}
            }
        elif block_type == "table":
            # Construir dict de tabla
            headers = []
            for c in range(self.table_widget.columnCount()):
                item = self.table_widget.horizontalHeaderItem(c)
                headers.append(item.text() if item else f"H{c+1}")
            
            data = []
            for r in range(self.table_widget.rowCount()):
                row_data = []
                for c in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(r, c)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            return {
                "type": "table",
                "content": {
                    "headers": headers,
                    "data": data
                },
                "parameters": {}
            }
        else:  # text
            return {
                "type": "text",
                "content": self.text_content.toPlainText(),
                "parameters": {"style": "Normal"}
            }
    
    def clear(self):
        """Limpia todos los campos."""
        self.heading_content.clear()
        self.heading_level.setValue(3)
        self.text_content.clear()
        self.equation_content.clear()


class SnippetEditorDialog(QDialog):
    """Diálogo principal para editar un snippet completo."""
    
    def __init__(self, parent=None, snippet_data=None, category=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Snippet")
        self.setMinimumSize(700, 500)
        
        self._original_id = snippet_data.get("id") if snippet_data else None
        self._category = category
        
        self._blocks = []
        
        self.setup_ui()
        
        if snippet_data:
            self.load_snippet(snippet_data)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Metadatos del snippet
        meta_group = QGroupBox("Metadatos")
        meta_form = QFormLayout()
        
        self.edit_id = QLineEdit()
        self.edit_id.setPlaceholderText("identificador_unico (sin espacios)")
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Título visible en la lista")
        self.edit_desc = QTextEdit()
        self.edit_desc.setMaximumHeight(60)
        self.edit_desc.setPlaceholderText("Descripción breve del contenido")
        
        meta_form.addRow("ID:", self.edit_id)
        meta_form.addRow("Título:", self.edit_title)
        meta_form.addRow("Descripción:", self.edit_desc)
        meta_group.setLayout(meta_form)
        layout.addWidget(meta_group)
        
        # Contenido (lista de bloques + editor)
        content_group = QGroupBox("Contenido")
        content_layout = QHBoxLayout()
        
        # Panel izquierdo: lista de bloques
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Bloques:"))
        self.list_blocks = QListWidget()
        self.list_blocks.currentRowChanged.connect(self._on_block_selected)
        left_panel.addWidget(self.list_blocks)
        
        # Botones de bloques
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+")
        btn_add.setFixedWidth(30)
        btn_add.setToolTip("Agregar bloque")
        btn_add.clicked.connect(self._add_block)
        
        btn_remove = QPushButton("-")
        btn_remove.setFixedWidth(30)
        btn_remove.setToolTip("Eliminar bloque")
        btn_remove.clicked.connect(self._remove_block)
        
        btn_up = QPushButton("^")
        btn_up.setFixedWidth(30)
        btn_up.setToolTip("Mover arriba")
        btn_up.clicked.connect(self._move_block_up)
        
        btn_down = QPushButton("v")
        btn_down.setFixedWidth(30)
        btn_down.setToolTip("Mover abajo")
        btn_down.clicked.connect(self._move_block_down)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_up)
        btn_layout.addWidget(btn_down)
        btn_layout.addStretch()
        left_panel.addLayout(btn_layout)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(200)
        
        # Panel derecho: editor de bloque
        self.block_editor = BlockEditor()
        self.block_editor.contentChanged.connect(self._on_block_content_changed)
        
        content_layout.addWidget(left_widget)
        content_layout.addWidget(self.block_editor, 1)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group, 1)
        
        # Botones de diálogo
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_snippet(self, data):
        """Carga los datos de un snippet existente."""
        self.edit_id.setText(data.get("id", ""))
        self.edit_title.setText(data.get("title", ""))
        self.edit_desc.setPlainText(data.get("description", ""))
        
        self._blocks = data.get("content", [])
        self._refresh_block_list()
        
        if self._blocks:
            self.list_blocks.setCurrentRow(0)
    
    def _refresh_block_list(self):
        """Actualiza la lista visual de bloques."""
        self.list_blocks.clear()
        for i, block in enumerate(self._blocks):
            btype = block.get("type", "?")
            raw_content = block.get("content", "")
            
            if isinstance(raw_content, str):
                content = raw_content[:30]
            elif isinstance(raw_content, dict):
                content = "[Estructura compleja]"
                if btype == "table":
                    content = "[Tabla]"
            else:
                content = str(raw_content)[:30]
                
            label = f"{i+1}. [{btype}] {content}..."
            self.list_blocks.addItem(label)
    
    def _on_block_selected(self, row):
        """Carga el bloque seleccionado en el editor."""
        if 0 <= row < len(self._blocks):
            self.block_editor.set_block(self._blocks[row])
    
    def _on_block_content_changed(self):
        """Guarda los cambios del editor en el bloque actual."""
        row = self.list_blocks.currentRow()
        if 0 <= row < len(self._blocks):
            # Obtener datos actualizados del editor
            block_data = self.block_editor.get_block()
            self._blocks[row] = block_data
            
            # Actualizar solo el texto del ítem en la lista (sin recrear lista)
            # Esto evita que se pierda el foco o se resetee el cursor en el editor
            item = self.list_blocks.item(row)
            if item:
                btype = block_data.get("type", "?")
                # Limpiar saltos de línea para el label
                content = block_data.get("content", "")[:30].replace("\n", " ")
                label = f"{row+1}. [{btype}] {content}..."
                item.setText(label)
    
    def _add_block(self):
        """Agrega un nuevo bloque vacío."""
        new_block = {"type": "text", "content": "", "parameters": {"style": "Normal"}}
        self._blocks.append(new_block)
        self._refresh_block_list()
        self.list_blocks.setCurrentRow(len(self._blocks) - 1)
    
    def _remove_block(self):
        """Elimina el bloque seleccionado."""
        row = self.list_blocks.currentRow()
        if 0 <= row < len(self._blocks):
            del self._blocks[row]
            self._refresh_block_list()
            if self._blocks:
                self.list_blocks.setCurrentRow(min(row, len(self._blocks) - 1))
            else:
                self.block_editor.clear()
    
    def _move_block_up(self):
        """Mueve el bloque seleccionado hacia arriba."""
        row = self.list_blocks.currentRow()
        if row > 0:
            self._blocks[row], self._blocks[row-1] = self._blocks[row-1], self._blocks[row]
            self._refresh_block_list()
            self.list_blocks.setCurrentRow(row - 1)
    
    def _move_block_down(self):
        """Mueve el bloque seleccionado hacia abajo."""
        row = self.list_blocks.currentRow()
        if 0 <= row < len(self._blocks) - 1:
            self._blocks[row], self._blocks[row+1] = self._blocks[row+1], self._blocks[row]
            self._refresh_block_list()
            self.list_blocks.setCurrentRow(row + 1)
    
    def _on_save(self):
        """Valida y acepta el diálogo."""
        # Validar campos requeridos
        if not self.edit_id.text().strip():
            QMessageBox.warning(self, "Validación", "El campo ID es requerido.")
            self.edit_id.setFocus()
            return
        
        if not self.edit_title.text().strip():
            QMessageBox.warning(self, "Validación", "El campo Título es requerido.")
            self.edit_title.setFocus()
            return
        
        self.accept()
    
    def get_snippet_data(self):
        """Retorna el snippet editado como diccionario."""
        return {
            "id": self.edit_id.text().strip(),
            "title": self.edit_title.text().strip(),
            "description": self.edit_desc.toPlainText().strip(),
            "content": self._blocks
        }
    
    def get_original_id(self):
        """Retorna el ID original (para actualización)."""
        return self._original_id
