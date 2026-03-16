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
        # 1. Structures
        struct_tab = QWidget()
        struct_layout = QHBoxLayout(struct_tab)
        struct_layout.setContentsMargins(4, 4, 4, 4)
        
        # Format: (Label, LaTeX Code, Display Text/Icon)
        struct_blocks = [
            ("Fracción", "\\frac{}{}", "½"),
            ("Índice", "^{}", "xʸ"),
            ("Subíndice", "_{}", "x_y"),
            ("Raíz", "\\sqrt{}", "√"),
            ("Raíz N", "\\sqrt[]{}", "ⁿ√"),
            ("Paréntesis", "\\left(  \\right)", "( )"),
            ("Corchetes", "\\left[  \\right]", "[ ]"),
            ("Llaves", "\\left\\{  \\right\\}", "{ }"),
            ("Valor Abs.", "\\left|  \\right|", "|x|")
        ]
        self._add_group(struct_layout, struct_blocks)
        self.addTab(struct_tab, "Estructuras")

        # 2. Calculus
        calc_tab = QWidget()
        calc_layout = QHBoxLayout(calc_tab)
        calc_layout.setContentsMargins(4, 4, 4, 4)

        calc_blocks = [
            ("Sumatoria", "\\sum", "∑"),
            ("Suma Lím", "\\sum_{}^{}", "∑lim"),
            ("Integral", "\\int", "∫"),
            ("Integral Lím", "\\int_{}^{}", "∫lim"),
            ("Productoria", "\\prod", "∏"),
            ("Límite", "\\lim", "lim"),
            ("Límite →", "\\lim_{ \\to }", "lim→"),
        ]
        self._add_group(calc_layout, calc_blocks)
        self.addTab(calc_tab, "Cálculo")

        # 3. Matrices
        matrix_tab = QWidget()
        matrix_layout = QHBoxLayout(matrix_tab)
        matrix_layout.setContentsMargins(4, 4, 4, 4)

        matrix_blocks = [
            ("Matriz", "\\begin{matrix} & \\\\ & \\end{matrix}", "(Mat)"),
            ("Vector Col", "\\begin{matrix}-\\\\-\\\\-\\ \\end{matrix}", "日"),
            ("Vector Fila", "\\begin{matrix}-&-&-\\ \\end{matrix}", "▭"),
            ("Alineado", "\\begin{aligned} &= \\\\ &= \\end{aligned}", "Align"),
        ]
        self._add_group(matrix_layout, matrix_blocks)
        self.addTab(matrix_tab, "Matrices")

        # 4. Operators
        ops_tab = QWidget()
        ops_layout = QGridLayout(ops_tab)
        ops_layout.setContentsMargins(4, 4, 4, 4)
        ops_layout.setSpacing(2)
        
        operators_list = [
            ("Igual", "=", "="), ("Distinto", "\\neq", "≠"), ("Aprox", "\\approx", "≈"), ("MenorIgual", "\\leq", "≤"),
            ("MayorIgual", "\\geq", "≥"), ("MasMenos", "\\pm", "±"), ("Por", "\\times", "×"), ("Div", "\\div", "÷"),
            ("Punto", "\\cdot", "⋅"), ("Flecha Der", "\\to", "→"), ("Implica", "\\Rightarrow", "⇒"), ("DobleFlecha", "\\leftrightarrow", "↔"),
            ("ParaTodo", "\\forall", "∀"), ("Existe", "\\exists", "∃"), ("Pertenece", "\\in", "∈"), ("NoPertenece", "\\notin", "∉"),
            ("Alpha", "\\alpha", "α"), ("Beta", "\\beta", "β"), ("Delta", "\\Delta", "Δ"), ("Pi", "\\pi", "π")
        ]

        row, col = 0, 0
        for name, code, label in operators_list:
            btn = QPushButton(label)
            btn.setFixedSize(40, 30)
            btn.setToolTip(f"{name} ({code})")
            btn.clicked.connect(lambda c=False, s=code: self.snippetClicked.emit(s))
            ops_layout.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1
        
        ops_layout.setRowStretch(row+1, 1)
        ops_layout.setColumnStretch(col+1, 1)
        self.addTab(ops_tab, "Operadores Simples")

    def _add_group(self, layout, items):
        """Helper para agregar botones al layout"""
        for label, snippet, icon_text in items:
            btn = QPushButton(icon_text + "\n" + label)
            btn.setFixedSize(60, 60)
            btn.setToolTip(label)
            btn.setStyleSheet("text-align: center; padding: 2px;")
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
            lbl = QLabel(category)
            lbl.setStyleSheet("font-size: 10px; color: #666; margin-top: 4px;")
            layout.addWidget(lbl)
            
            grid = QGridLayout()
            grid.setSpacing(1)
            
            col = 0
            row = 0
            max_cols = 5 if category == "Estructuras" else 6
            
            for latex_cmd, display in syms.items():
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
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guía Rápida UnicodeMath")
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Sintaxis UnicodeMath para Word")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        examples = {
            "Fracciones": [
                ("(a)/(b)", "Fracción simple"),
                ("(a+b)/(c+d)", "Fracción con expresiones"),
                ("(1)/(2)+(3)/(4)", "Suma de fracciones"),
            ],
        }
        
        for category, items in examples.items():
            cat_label = QLabel(category)
            cat_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333; margin-top: 5px;")
            content_layout.addWidget(cat_label)
            
            grid = QGridLayout()
            grid.setColumnStretch(0, 2)
            grid.setColumnStretch(1, 3)
            grid.setSpacing(4)
            
            for row, (code, desc) in enumerate(items):
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
                
                desc_label = QLabel(desc)
                desc_label.setStyleSheet("font-size: 11px; color: #666;")
                grid.addWidget(desc_label, row, 1)
            
            content_layout.addLayout(grid)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        note = QLabel("💡 Tip: Escribe \\alpha, \\beta, etc. y se convertirán automáticamente a símbolos Unicode")
        note.setStyleSheet("font-size: 11px; color: #666; font-style: italic; margin-top: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copiado", f"'{text}' copiado al portapapeles")
