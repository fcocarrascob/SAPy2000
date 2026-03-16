"""
themes.py — Sistema de temas centralizado para SAP2000 Automation Suite.

Define paleta de colores modo claro, esquemas para botones/tabs/inputs,
y función apply_theme(app) que configura QPalette + stylesheet global.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


# ======================================================================
# Paleta de colores — Modo Claro Profesional
# ======================================================================

COLORS = {
    # Fondos
    "bg_window":        "#F5F5F5",
    "bg_base":          "#FFFFFF",
    "bg_alt":           "#FAFAFA",
    "bg_card":          "#FFFFFF",

    # Texto
    "text_primary":     "#212121",
    "text_secondary":   "#616161",
    "text_disabled":    "#9E9E9E",
    "text_placeholder": "#BDBDBD",

    # Acentos
    "primary":          "#1565C0",      # Azul profesional
    "primary_light":    "#1E88E5",
    "primary_dark":     "#0D47A1",
    "primary_surface":  "#E3F2FD",

    "success":          "#2E7D32",
    "success_light":    "#4CAF50",
    "success_surface":  "#E8F5E9",

    "warning":          "#E65100",
    "warning_light":    "#FF9800",
    "warning_surface":  "#FFF3E0",

    "error":            "#C62828",
    "error_light":      "#EF5350",
    "error_surface":    "#FFEBEE",

    # Bordes y separadores
    "border":           "#E0E0E0",
    "border_focus":     "#1565C0",
    "divider":          "#EEEEEE",

    # Componentes
    "tab_active_bg":    "#FFFFFF",
    "tab_inactive_bg":  "#EEEEEE",
    "toolbar_bg":       "#FAFAFA",
    "statusbar_bg":     "#F5F5F5",
    "groupbox_border":  "#CFD8DC",

    # Botones variantes
    "btn_secondary_bg":     "#E0E0E0",
    "btn_secondary_hover":  "#BDBDBD",
    "btn_secondary_text":   "#424242",
}


# ======================================================================
# Stylesheet global
# ======================================================================

def _build_stylesheet() -> str:
    c = COLORS
    return f"""
    /* ---- Ventana principal ---- */
    QMainWindow, QDialog {{
        background-color: {c['bg_window']};
    }}

    /* ---- Widgets base ---- */
    QWidget {{
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 13px;
        color: {c['text_primary']};
    }}

    /* ---- Toolbar ---- */
    QToolBar {{
        background-color: {c['toolbar_bg']};
        border-bottom: 1px solid {c['border']};
        padding: 4px 8px;
        spacing: 6px;
    }}

    /* ---- Status bar ---- */
    QStatusBar {{
        background-color: {c['statusbar_bg']};
        border-top: 1px solid {c['border']};
        color: {c['text_secondary']};
        font-size: 12px;
    }}

    /* ---- Tab Widget ---- */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background-color: {c['bg_base']};
    }}
    QTabBar::tab {{
        background-color: {c['tab_inactive_bg']};
        color: {c['text_secondary']};
        padding: 8px 18px;
        border: 1px solid {c['border']};
        border-bottom: none;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['tab_active_bg']};
        color: {c['primary']};
        font-weight: bold;
        border-bottom: 2px solid {c['primary']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['primary_surface']};
    }}

    /* ---- Group Box ---- */
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {c['groupbox_border']};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 18px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        top: 2px;
        padding: 0 6px;
        color: {c['primary']};
    }}

    /* ---- Inputs ---- */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 8px;
        background-color: {c['bg_base']};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c['border_focus']};
    }}
    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {c['bg_alt']};
        color: {c['text_disabled']};
    }}

    /* ---- ComboBox ---- */
    QComboBox {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 5px 8px;
        background-color: {c['bg_base']};
    }}
    QComboBox:focus {{
        border: 2px solid {c['border_focus']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    /* ---- Table ---- */
    QTableWidget {{
        background-color: {c['bg_base']};
        gridline-color: {c['divider']};
        border: 1px solid {c['border']};
        border-radius: 4px;
    }}
    QTableWidget::item:selected {{
        background-color: {c['primary_surface']};
        color: {c['text_primary']};
    }}
    QHeaderView::section {{
        background-color: {c['bg_alt']};
        color: {c['text_primary']};
        font-weight: bold;
        padding: 6px;
        border: none;
        border-bottom: 2px solid {c['primary']};
        border-right: 1px solid {c['divider']};
    }}

    /* ---- Buttons (base) ---- */
    QPushButton {{
        background-color: {c['btn_secondary_bg']};
        color: {c['btn_secondary_text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['btn_secondary_hover']};
    }}
    QPushButton:pressed {{
        background-color: #AAAAAA;
    }}
    QPushButton:disabled {{
        background-color: {c['bg_alt']};
        color: {c['text_disabled']};
        border-color: {c['divider']};
    }}

    /* ---- Scroll Area ---- */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* ---- Text Edit (logs) ---- */
    QTextEdit {{
        background-color: {c['bg_base']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
    }}

    /* ---- ProgressBar ---- */
    QProgressBar {{
        border: 1px solid {c['border']};
        border-radius: 4px;
        text-align: center;
        height: 22px;
        background-color: {c['bg_alt']};
    }}
    QProgressBar::chunk {{
        background-color: {c['primary']};
        border-radius: 3px;
    }}

    /* ---- Label informativo ---- */
    QLabel[role="info"] {{
        color: {c['text_secondary']};
        font-style: italic;
        font-size: 12px;
    }}

    /* ---- Splitter ---- */
    QSplitter::handle {{
        background-color: {c['divider']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    """


# ======================================================================
# Estilos para variantes de botones (aplicar vía setStyleSheet individual)
# ======================================================================

BUTTON_STYLES = {
    "primary": f"""
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['primary_light']}; }}
        QPushButton:pressed {{ background-color: {COLORS['primary_dark']}; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "success": f"""
        QPushButton {{
            background-color: {COLORS['success']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['success_light']}; }}
        QPushButton:pressed {{ background-color: #1B5E20; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "warning": f"""
        QPushButton {{
            background-color: {COLORS['warning']};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {COLORS['warning_light']}; }}
        QPushButton:pressed {{ background-color: #BF360C; }}
        QPushButton:disabled {{ background-color: {COLORS['bg_alt']}; color: {COLORS['text_disabled']}; }}
    """,
    "secondary": f"""
        QPushButton {{
            background-color: {COLORS['btn_secondary_bg']};
            color: {COLORS['btn_secondary_text']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ background-color: {COLORS['btn_secondary_hover']}; }}
        QPushButton:pressed {{ background-color: #AAAAAA; }}
    """,
}


# ======================================================================
# Función principal — aplicar tema a la app
# ======================================================================

def apply_theme(app: QApplication):
    """
    Aplica el tema visual completo a la aplicación.
    Llamar después de app.setStyle('Fusion').
    """
    # 1. QPalette base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS["bg_window"]))
    palette.setColor(QPalette.WindowText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Base, QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS["bg_alt"]))
    palette.setColor(QPalette.Text, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.PlaceholderText, QColor(COLORS["text_placeholder"]))
    palette.setColor(QPalette.Button, QColor(COLORS["btn_secondary_bg"]))
    palette.setColor(QPalette.ButtonText, QColor(COLORS["btn_secondary_text"]))
    palette.setColor(QPalette.Highlight, QColor(COLORS["primary"]))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipBase, QColor(COLORS["bg_base"]))
    palette.setColor(QPalette.ToolTipText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.Light, QColor("#FFFFFF"))
    palette.setColor(QPalette.Midlight, QColor(COLORS["bg_alt"]))
    palette.setColor(QPalette.Mid, QColor(COLORS["border"]))
    palette.setColor(QPalette.Dark, QColor(COLORS["text_secondary"]))

    app.setPalette(palette)

    # 2. Stylesheet global
    app.setStyleSheet(_build_stylesheet())