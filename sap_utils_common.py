"""
sap_utils_common.py — Funciones utilitarias compartidas para la SAP2000 API.

Provee:
- check_ret_code(ret): Validador universal de retornos comtypes
- safe_sap_call(func, *args): Wrapper con manejo de errores automático
- get_materials_by_type(sap_model, mat_type): Extractor de materiales por tipo
- create_point_safe(sap_model, x, y, z, name): Creador de puntos con validación
"""

from typing import Any, Optional, Tuple, List

from app_logger import AppLogger


def check_ret_code(ret) -> bool:
    """
    Validador universal para retornos de la API SAP2000 vía comtypes.

    La API retorna TUPLAS donde el último elemento es el código de retorno.
    ret[-1] == 0 indica éxito.

    También maneja el caso donde la función retorna un entero directo.

    Args:
        ret: Resultado de una llamada a la API SAP2000. Puede ser:
             - tuple/list: ret[-1] es el código de retorno
             - int: el valor directo es el código de retorno

    Returns:
        True si el código de retorno indica éxito (0), False en caso contrario.
    """
    if ret is None:
        return False
    if isinstance(ret, (tuple, list)):
        return len(ret) > 0 and ret[-1] == 0
    if isinstance(ret, int):
        return ret == 0
    return False


def safe_sap_call(func, *args, default=None, description: str = ""):
    """
    Wrapper para llamadas a la API SAP2000 con manejo de errores automático.

    Args:
        func: Función/método de la API SAP2000 a ejecutar
        *args: Argumentos para la función
        default: Valor a retornar en caso de error
        description: Descripción legible de la operación (para logs)

    Returns:
        El resultado de la llamada si exitosa, o *default* si falla.
    """
    logger = AppLogger()
    try:
        ret = func(*args)
        if check_ret_code(ret):
            return ret
        else:
            if description:
                logger.warning(f"{description}: código de retorno indica fallo")
            return default
    except Exception as e:
        if description:
            logger.error(f"{description}: {e}")
        return default


def get_materials_by_type(sap_model, mat_type: int) -> List[str]:
    """
    Obtiene la lista de materiales filtrados por tipo desde SAP2000.

    Args:
        sap_model: Objeto SapModel conectado
        mat_type: Tipo de material según API SAP2000:
                  1 = Steel, 2 = Concrete, 3 = NoDesign,
                  4 = Aluminum, 5 = ColdFormed, 6 = Rebar

    Returns:
        Lista de nombres de materiales del tipo especificado.
    """
    if not sap_model:
        return []

    try:
        ret = sap_model.PropMaterial.GetNameList()
        if not check_ret_code(ret):
            return []

        count = ret[0]
        names = ret[1]

        if count == 0:
            return []

        # Normalizar: si count == 1, names puede ser str en vez de tuple
        if isinstance(names, str):
            names = (names,)

        result = []
        for name in names:
            try:
                type_ret = sap_model.PropMaterial.GetTypeOAPI(name)
                if check_ret_code(type_ret) and type_ret[0] == mat_type:
                    result.append(name)
            except Exception:
                continue

        return result

    except Exception:
        return []


def create_point_safe(
    sap_model, x: float, y: float, z: float, name: str = ""
) -> Optional[str]:
    """
    Crea un punto en SAP2000 con validación y manejo de errores.

    Args:
        sap_model: Objeto SapModel conectado
        x, y, z: Coordenadas del punto
        name: Nombre asignado al punto (vacío = autogenerado)

    Returns:
        Nombre del punto creado, o None si falla.
    """
    if not sap_model:
        return None

    logger = AppLogger()
    try:
        ret = sap_model.PointObj.AddCartesian(x, y, z, "", name, "Global")
        if check_ret_code(ret):
            return ret[0] if isinstance(ret, (tuple, list)) else name
        else:
            logger.warning(f"No se pudo crear punto ({x}, {y}, {z})")
            return None
    except Exception as e:
        logger.error(f"Error al crear punto ({x}, {y}, {z}): {e}")
        return None