"""
gui_components.py — Componentes GUI reutilizables para SAP2000 Automation Suite.

Provee widgets estandarizados:
- StyledButton: Botón con variantes de color (primary, success, warning, secondary)
- LogWidget: Área de log con auto-scroll y timestamp
- ProgressGroup: QGroupBox con QProgressBar + QLabel de estado
- ConnectionStatusWidget: Indicador visual de conexión SAP2000
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QPushButton, QGroupBox, QVBoxLayout, QHBoxLayout,
    QProgressBar, QLabel, QTextEdit, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from themes import BUTTON_STYLES, COLORS


# ======================================================================
# StyledButton
# ======================================================================

class StyledButton(QPushButton):
    """
    QPushButton con estilo preconfigurado por variante.

    Variantes: 'primary', 'success', 'warning', 'secondary'

    Uso:
        btn = StyledButton("📥 Leer SAP2000", variant="primary")
    """

    def __init__(self, text: str = "", variant: str = "secondary", parent=None):
        super().__init__(text, parent)
        style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
        self.setStyleSheet(style)
        self._variant = variant

    def set_variant(self, variant: str):
        """Cambia la variante visual del botón."""
        style = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
        self.setStyleSheet(style)
        self._variant = variant


# ======================================================================
# LogWidget
# ======================================================================

class LogWidget(QTextEdit):
    """
    Área de log de solo lectura con auto-scroll y formato de timestamp.

    Uso:
        log = LogWidget()
        log.log("Operación completada", level="SUCCESS")
    """

    _LEVEL_COLORS = {
        "INFO":    COLORS["text_secondary"],
        "SUCCESS": COLORS["success"],
        "WARNING": COLORS["warning"],
        "ERROR":   COLORS["error"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def log(self, message: str, level: str = "INFO"):
        """Agrega una línea al log con timestamp y color por nivel."""
        ts = datetime.now().strftime("%H:%M:%S")
        prefixes = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        prefix = prefixes.get(level, "")
        color = self._LEVEL_COLORS.get(level, COLORS["text_primary"])
        html = f'<span style="color:{color}">[{ts}] {prefix} {message}</span>'
        self.append(html)
        # Auto-scroll al final
        self.moveCursor(QTextCursor.End)

    def clear_log(self):
        """Limpia todo el contenido del log."""
        self.clear()


# ======================================================================
# ProgressGroup
# ======================================================================

class ProgressGroup(QGroupBox):
    """
    QGroupBox con QProgressBar y QLabel de estado.

    Uso:
        pg = ProgressGroup("Progreso")
        pg.set_progress(45, "Creando nudos...")
        pg.set_visible(True)
    """

    def __init__(self, title: str = "Progreso", parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-style: italic; font-size: 12px;"
        )
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setVisible(False)

    def set_progress(self, value: int, message: str = ""):
        """Actualiza la barra y el mensaje de estado."""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)

    def reset(self):
        """Reinicia la barra y oculta el grupo."""
        self.progress_bar.setValue(0)
        self.status_label.setText("")
        self.setVisible(False)

    def set_visible(self, visible: bool):
        """Muestra u oculta el grupo de progreso."""
        self.setVisible(visible)


# ======================================================================
# ConnectionStatusWidget
# ======================================================================

class ConnectionStatusWidget(QWidget):
    """
    Indicador visual del estado de conexión con SAP2000.
    Muestra un punto de color + texto de estado.

    Uso:
        csw = ConnectionStatusWidget()
        csw.set_connected(True)   # Verde: "Conectado a SAP2000"
        csw.set_connected(False)  # Rojo: "Desconectado"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 2, 8, 2)

        self._indicator = QLabel("●")
        self._indicator.setFixedWidth(18)
        layout.addWidget(self._indicator)

        self._label = QLabel("Desconectado")
        layout.addWidget(self._label)

        self.setLayout(layout)
        self.set_connected(False)

    def set_connected(self, connected: bool):
        """Actualiza el indicador visual según el estado de conexión."""
        if connected:
            self._indicator.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 16px;"
            )
            self._label.setText("Conectado a SAP2000")
            self._label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        else:
            self._indicator.setStyleSheet(
                f"color: {COLORS['error']}; font-size: 16px;"
            )
            self._label.setText("Desconectado")
            self._label.setStyleSheet(f"color: {COLORS['text_secondary']};")