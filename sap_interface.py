import sys
import comtypes.client
from PySide6.QtCore import QObject, Signal

class SapInterface(QObject):
    """
    Gestiona la conexión única con la API de SAP2000.
    Emite señales cuando el estado de la conexión cambia.
    """
    connectionChanged = Signal(bool) # True: Conectado, False: Desconectado

    def __init__(self):
        super().__init__()
        self.SapModel = None
        self.SapObject = None

    def connect_to_sap(self):
        """Intenta conectar a una instancia activa de SAP2000."""
        try:
            # Obtener el objeto activo de SAP2000
            self.SapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
            self.SapModel = self.SapObject.SapModel
            
            # Verificar si realmente estamos conectados intentando una llamada simple
            self.SapModel.GetModelFilename()
            
            print("Conexión exitosa con SAP2000.")
            self.connectionChanged.emit(True)
            return True
        except Exception as e:
            print(f"No se pudo conectar a SAP2000: {e}")
            self.SapModel = None
            self.SapObject = None
            self.connectionChanged.emit(False)
            return False

    def disconnect(self):
        """Limpia la referencia a la conexión."""
        self.SapModel = None
        self.SapObject = None
        self.connectionChanged.emit(False)
        print("Desconectado de SAP2000.")

    def is_connected(self):
        return self.SapModel is not None
