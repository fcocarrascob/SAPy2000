import sys
import comtypes.client
from PySide6.QtCore import QObject, Signal
from app_logger import AppLogger


class SapInterface(QObject):
    """
    Gestiona la conexión única con la API de SAP2000.
    Emite señales cuando el estado de la conexión cambia.
    """
    connectionChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self.SapModel = None
        self.SapObject = None
        self.logger = AppLogger()

    def connect_to_sap(self):
        """Intenta conectar a una instancia activa de SAP2000."""
        try:
            self.logger.info("Intentando conectar a SAP2000...")
            self.SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            self.SapModel = self.SapObject.SapModel

            # Verificar conexión con llamada simple
            self.SapModel.GetModelFilename()

            self.logger.success("Conexión exitosa con SAP2000")
            self.connectionChanged.emit(True)
            return True
        except Exception as e:
            self.logger.error(f"No se pudo conectar a SAP2000: {e}")
            self.SapModel = None
            self.SapObject = None
            self.connectionChanged.emit(False)
            return False

    def disconnect(self):
        """Limpia la referencia a la conexión."""
        self.SapModel = None
        self.SapObject = None
        self.connectionChanged.emit(False)
        self.logger.info("Desconectado de SAP2000")

    def reconnect(self):
        """Intenta reconectar a SAP2000 (útil si se pierde la conexión)."""
        self.logger.info("Intentando reconectar...")
        self.SapModel = None
        self.SapObject = None
        return self.connect_to_sap()

    def is_connected(self):
        return self.SapModel is not None