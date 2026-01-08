# Instrucciones para GitHub Copilot - SAP2000 API con comtypes

Estás trabajando en un proyecto de Python que interactúa con la API de SAP2000 (CSI OAPI) utilizando la librería `comtypes`. La aplicación se ha migrado a una arquitectura unificada y modular.

## Reglas Críticas de Implementación

### 1. Manejo de Retornos (La Regla de Oro)
La API de SAP2000 está diseñada para lenguajes que soportan parámetros `ByRef` (como VBA o C#). En Python con `comtypes`, el comportamiento es diferente:

*   **NO** asumas que los parámetros de entrada se modifican in-place.
*   Las funciones retornan una **TUPLA** o **LISTA** que contiene todos los valores de salida definidos como `ByRef` en la documentación original, seguidos por el valor de retorno de la función.
*   **El último elemento** de la lista de retorno es SIEMPRE el código de estado (`RetCode`). `0` significa éxito.

### 2. Patrón de Código Obligatorio

**Incorrecto (Estilo VBA/C#):**
```python
# NO HACER ESTO
ret = SapModel.Func(param_in, param_out)
if ret != 0: ...
```

**Correcto (Estilo Python comtypes):**
```python
# HACER ESTO: Desempaquetar o acceder por índice
ret = SapModel.Func(param_in, 0, []) 

# ret es [ValorSalida1, ValorSalida2, ..., RetCode]

if ret[-1] == 0: # Verificar éxito (último elemento)
    resultado_1 = ret[0]
else:
    print(f"Error en la función, código: {ret[-1]}")
```

### 3. Conexión y Arquitectura (NUEVO)
**No utilices GetActiveObject dentro de los módulos individuales.** La aplicación utiliza una arquitectura de **Inyección de Dependencias**.

#### Backends
*   Deben ser clases que reciban `sap_model` en su `__init__`.
*   No deben depender de librerías GUI (PySide6).

```python
class MiModuloBackend:
    def __init__(self, sap_model):
        self.SapModel = sap_model

    def ejecutar_tarea(self):
        if not self.SapModel: return
        # Lógica OAPI...
```

#### Frontend (GUI)
*   Deben ser Widgets (`QWidget`) que reciban `sap_interface` en su `__init__`.
*   Usan `sap_interface.sap_model` para instanciar el backend.

```python
class MiModuloWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface

    def on_button_click(self):
        model = self.sap_interface.sap_model
        backend = MiModuloBackend(model)
        backend.ejecutar_tarea()
```

### 4. Estructura de Módulos
Para crear una nueva herramienta:
1.  Crea una carpeta nueva con `__init__.py`.
2.  Crea un archivo `backend.py` con la lógica agnóstica.
3.  Crea un archivo `gui.py` con la interfaz visual.
4.  Registra el widget en `main_app.py`.

### 5. Documentación de la API
La documentación y ejemplos de la API de SAP2000 están disponibles en la carpeta `API` del repositorio.
