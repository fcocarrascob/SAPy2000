# File: sap2000_connector.py
# Módulo para conectar a una instancia activa de SAP2000 usando comtypes (CSI OAPI).
import sys
import comtypes.client
from typing import Tuple, Optional, Any, Sequence

def get_active_sap2000() -> Tuple[Optional[Any], Optional[Any]]:
    """
    Intenta conectar a una instancia activa de SAP2000 y devuelve (mySapObject, SapModel).
    Si no hay instancia, devuelve (None, None).
    """
    try:
        mySapObject = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject")
        SapModel = mySapObject.SapModel
        return mySapObject, SapModel
    except OSError:
        return None, None

def connect_or_exit() -> Tuple[Any, Any]:
    """
    Igual que get_active_sap2000 pero sale del proceso si no se encuentra SAP2000.
    """
    mySapObject, SapModel = get_active_sap2000()
    if mySapObject is None:
        print("No se encontró una instancia activa de SAP2000. Por favor abre SAP2000 manualmente primero.")
        sys.exit(-1)
    return mySapObject, SapModel

def check_ret(ret: Sequence, raise_on_error: bool = False, context: str = "") -> Optional[Sequence]:
    """
    Manejo estándar de retornos de funciones comtypes/SAP2000:
    - ret es una tupla/lista donde el último elemento es el código de retorno (0 = éxito).
    - Devuelve los valores de salida (todos menos el último) si éxito.
    - Si hay error, imprime o lanza RuntimeError según raise_on_error.
    """
    if not isinstance(ret, (list, tuple)):
        # Algunas llamadas pueden devolver solo un código; normalizar a tupla
        return None if ret != 0 else ()
    code = ret[-1]
    if code != 0:
        msg = f"Error en API SAP2000{(' - ' + context) if context else ''}. Código: {code}"
        if raise_on_error:
            raise RuntimeError(msg)
        print(msg)
        return None
    return tuple(ret[:-1])

# Ejemplo rápido de uso (puede eliminarse en producción):
if __name__ == "__main__":
    obj, model = get_active_sap2000()
    if obj:
        print("Conectado a SAP2000")
    else:
        print("No hay instancia activa de SAP2000")