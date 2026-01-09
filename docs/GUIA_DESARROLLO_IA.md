# Guía de Implementación de Nuevos Módulos con Asistencia de IA

Este documento define el flujo de trabajo estándar para agregar nuevas funcionalidades o módulos al proyecto `SAPy2000`. Sigue esta guía para mantener la arquitectura limpia, modular y fácil de probar.

## Filosofía de Desarrollo: "Aislado -> Integrado"

Para evitar romper la aplicación principal (`main_app.py`), cada nuevo módulo debe desarrollarse y probarse como una "mini-aplicación" independiente antes de integrarse.

---

## Paso 1: Estructura de Archivos

Solicita a la IA crear una nueva carpeta para el módulo (ej. `Nuevo_Modulo`).
La estructura **obligatoria** es:

```text
SAPy2000/
└── Nuevo_Modulo/
    ├── __init__.py          # Archivo vacío para convertirlo en paquete
    ├── backend.py           # Lógica pura (comtypes/CSI API)
    └── gui.py               # Interfaz gráfica (PySide6)
```

---

## Paso 2: Plantilla del Backend (`backend.py`)

El backend debe ser agnósticado de la interfaz gráfica. Debe aceptar el modelo SAP (`sap_model`) en su constructor para permitir la **Inyección de Dependencias**.

**Prompt para la IA:**
> "Crea el archivo `backend.py` para el módulo `[Nombre]`. Usa la clase `[Nombre]Backend`. Debe aceptar `sap_model` en `__init__`. Si no se pasa modelo, debe intentar conectar con `GetActiveObject` para pruebas aisladas. Incluye un bloque `if __name__ == '__main__':` para probar un método básico."

**Plantilla de Código:**

```python
import comtypes.client

class NuevoModuloBackend:
    def __init__(self, sap_model=None):
        # 1. Inyección de dependencia (Producción)
        if sap_model:
            self.SapModel = sap_model
        else:
            # 2. Conexión Standalone (Desarrollo/Testing)
            try:
                self.SapModel = comtypes.client.GetActiveObject("CSI.SAP2000.API.SapObject").SapModel
                print("Backend conectado en modo Standalone")
            except Exception as e:
                self.SapModel = None
                print(f"No se pudo conectar al API: {e}")

    def mi_funcionalidad(self):
        if not self.SapModel:
            print("Error: No hay conexión a SAP2000")
            return

        # --- Lógica OAPI ---
        # Recordar la regla de oro de retornos: ret = func(in, 0, [])
        pass

if __name__ == "__main__":
    # Bloque de prueba unitaria
    backend = NuevoModuloBackend()
    backend.mi_funcionalidad()
```

---

## Paso 3: Plantilla de la GUI (`gui.py`)

La GUI debe ser un `QWidget`. Debe aceptar `sap_interface` para coordinarse con la app principal, pero manejar el caso `None` para pruebas aisladas.

**Prompt para la IA:**
> "Crea el archivo `gui.py` con una clase `[Nombre]Widget(QWidget)`. En `__init__` acepta `sap_interface`. Conecta un botón al backend. Asegúrate de que el backend se instancie usando `self.sap_interface.SapModel` si existe. Incluye un bloque `if __name__` para lanzar la ventana sola."

**Plantilla de Código:**

```python
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QApplication, QMessageBox
# Importación relativa (puntito) para cuando se usa como módulo
# Importación absoluta para pruebas directas (manejo de try/except opcional o correr como modulo)
try:
    from .backend import NuevoModuloBackend
except ImportError:
    from backend import NuevoModuloBackend

class NuevoModuloWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        btn = QPushButton("Ejecutar Acción", self)
        btn.clicked.connect(self.run_logic)
        layout.addWidget(btn)

    def run_logic(self):
        # Resolver el modelo: Integrado vs Standalone
        model = None
        if self.sap_interface and self.sap_interface.SapModel:
            model = self.sap_interface.SapModel
        
        # Instanciar backend (si model es None, el backend intentará conectar solo)
        backend = NuevoModuloBackend(sap_model=model)
        backend.mi_funcionalidad()

if __name__ == "__main__":
    # Prueba aislada de la GUI
    app = QApplication(sys.argv)
    window = NuevoModuloWidget() # sap_interface=None por defecto
    window.setWindowTitle("Prueba Aislada - Nuevo Módulo")
    window.show()
    sys.exit(app.exec())
```

---

## Paso 4: Pruebas (Antes de integrar)

Antes de modificar `main_app.py`, instruye a la IA para probar los componentes.

1.  **Prueba de Backend:**
    Ejecutar el script directamente para verificar conexión y lógica OAPI.
    ```bash
    python Nuevo_Modulo/backend.py
    ```

2.  **Prueba de GUI:**
    Ejecutar la GUI como módulo par ver si la ventana carga y el botón funciona.
    ```bash
    python -m Nuevo_Modulo.gui
    ```

---

## Paso 5: Integración

Solo cuando el paso 4 es exitoso, pide a la IA que integre el módulo.

**Prompt para la IA:**
> "El módulo `Nuevo_Modulo` funciona correctamente. Por favor intégralo en `main_app.py`. Importa el widget y agrégalo como una nueva pestaña en el método `init_tabs`, pasando `self.sap_interface`."

**Código a inyectar en `main_app.py`:**

```python
# 1. Importar
from Nuevo_Modulo.gui import NuevoModuloWidget

# 2. Agregar a init_tabs
try:
    self.new_tab = NuevoModuloWidget(sap_interface=self.sap_interface)
    self.tabs.addTab(self.new_tab, "Nombre Pestaña")
except Exception as e:
    self.tabs.addTab(QLabel(f"Error: {e}"), "Nombre (Error)")
```
