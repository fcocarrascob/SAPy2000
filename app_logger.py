"""
app_logger.py — Sistema de logging unificado para SAP2000 Automation Suite.

Singleton AppLogger con niveles INFO, WARNING, ERROR, SUCCESS.
Formato consistente con timestamp y prefijo visual.
Opción de exportar log a archivo.
"""

import os
from datetime import datetime
from typing import Optional, List, Callable


class AppLogger:
    """
    Logger singleton para toda la aplicación.
    Almacena mensajes en memoria y opcionalmente escribe a archivo.
    Soporta callbacks para conectar con LogWidget de GUI.
    """

    _instance: Optional["AppLogger"] = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._entries: List[str] = []
        self._callbacks: List[Callable[[str, str], None]] = []
        self._log_file: Optional[str] = None

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------

    def set_log_file(self, path: str):
        """Define ruta de archivo para persistencia de logs."""
        self._log_file = path

    def add_callback(self, cb: Callable[[str, str], None]):
        """
        Registra un callback que se invoca en cada mensaje.
        Firma: cb(level: str, formatted_message: str)
        """
        if cb not in self._callbacks:
            self._callbacks.append(cb)

    def remove_callback(self, cb: Callable[[str, str], None]):
        """Elimina un callback previamente registrado."""
        if cb in self._callbacks:
            self._callbacks.remove(cb)

    # ------------------------------------------------------------------
    # Emisión de mensajes
    # ------------------------------------------------------------------

    def _emit(self, level: str, prefix: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {prefix} {message}"
        self._entries.append(formatted)

        # Consola
        print(formatted)

        # Archivo (si configurado)
        if self._log_file:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except OSError:
                pass

        # Callbacks (GUI LogWidget, etc.)
        for cb in self._callbacks:
            try:
                cb(level, formatted)
            except Exception:
                pass

    def info(self, message: str):
        self._emit("INFO", "ℹ️", message)

    def success(self, message: str):
        self._emit("SUCCESS", "✅", message)

    def warning(self, message: str):
        self._emit("WARNING", "⚠️", message)

    def error(self, message: str):
        self._emit("ERROR", "❌", message)

    # ------------------------------------------------------------------
    # Consulta y exportación
    # ------------------------------------------------------------------

    def get_entries(self) -> List[str]:
        """Retorna copia de todas las entradas del log."""
        return list(self._entries)

    def clear(self):
        """Limpia las entradas en memoria (no afecta el archivo)."""
        self._entries.clear()

    def export_to_file(self, path: str) -> bool:
        """Exporta el log completo a un archivo de texto."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._entries))
            return True
        except OSError:
            return False

    @classmethod
    def reset(cls):
        """Resetea el singleton (útil para testing)."""
        cls._instance = None