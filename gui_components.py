"""
gui_components.py — Componentes GUI reutilizables para SAP2000 Automation Suite.

Provee widgets estandarizados:
- StyledButton: Botón con variantes de color (primary, success, warning, secondary)
- LogWidget: Área de log con auto-scroll y timestamp
- ProgressGroup: QGroupBox con QProgressBar + QLabel de estado
- ConnectionStatusWidget: Indicador visual de conexión SAP2000
"""

from datetime import datetime
from html import escape
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
        html = f'<span style="color:{color}">[{ts}] {prefix} {escape(message)}</span>'
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


# ======================================================================
# InputValidator
# ======================================================================

class InputValidator:
    """
    Validadores reutilizables para inputs de formularios.

    Uso:
        ok, msg = InputValidator.validate_numeric("12.5", min_val=0, max_val=100)
        ok, msg = InputValidator.validate_required("")
        ok, msg = InputValidator.validate_positive("0")
    """

    @staticmethod
    def validate_required(value: str, field_name: str = "Campo") -> tuple:
        """Valida que el valor no esté vacío."""
        if not value or not str(value).strip():
            return False, f"{field_name} es requerido."
        return True, ""

    @staticmethod
    def validate_numeric(
        value: str, field_name: str = "Valor",
        min_val: float = None, max_val: float = None,
    ) -> tuple:
        """Valida que el valor sea numérico y esté dentro del rango."""
        if not value or not str(value).strip():
            return False, f"{field_name} es requerido."
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False, f"{field_name} debe ser un número válido."

        if min_val is not None and num < min_val:
            return False, f"{field_name} debe ser ≥ {min_val}."
        if max_val is not None and num > max_val:
            return False, f"{field_name} debe ser ≤ {max_val}."
        return True, ""

    @staticmethod
    def validate_positive(value: str, field_name: str = "Valor") -> tuple:
        """Valida que el valor sea un número positivo (> 0)."""
        ok, msg = InputValidator.validate_numeric(value, field_name)
        if not ok:
            return ok, msg
        if float(value) <= 0:
            return False, f"{field_name} debe ser mayor que 0."
        return True, ""

    @staticmethod
    def validate_coordinates(x: str, y: str, z: str) -> tuple:
        """Valida que las tres coordenadas sean números válidos."""
        for label, val in [("X", x), ("Y", y), ("Z", z)]:
            ok, msg = InputValidator.validate_numeric(val, field_name=f"Coordenada {label}")
            if not ok:
                return False, msg
        return True, ""

    @staticmethod
    def validate_batch(validations: list) -> tuple:
        """
        Ejecuta múltiples validaciones y retorna el primer error.

        Args:
            validations: Lista de tuplas (ok: bool, msg: str)

        Returns:
            (True, "") si todo pasó, o (False, primer_error) si alguno falla.
        """
        for ok, msg in validations:
            if not ok:
                return False, msg
        return True, ""


# ======================================================================
# Helpers de Diálogo
# ======================================================================

from PySide6.QtWidgets import QMessageBox


def confirm_action(parent, title: str, message: str, detail: str = "") -> bool:
    """
    Muestra un diálogo de confirmación antes de una operación importante.

    Args:
        parent: Widget padre para el diálogo
        title: Título del diálogo
        message: Mensaje principal
        detail: Texto de detalle (opcional, aparece en área expandible)

    Returns:
        True si el usuario confirma, False si cancela.
    """
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    if detail:
        box.setDetailedText(detail)
    return box.exec() == QMessageBox.Yes


def show_validation_errors(parent, errors: list):
    """
    Muestra un diálogo con los errores de validación.

    Args:
        parent: Widget padre
        errors: Lista de strings con mensajes de error
    """
    if not errors:
        return
    msg = "Se encontraron los siguientes problemas:\n\n"
    msg += "\n".join(f"• {e}" for e in errors)
    QMessageBox.warning(parent, "Validación", msg)