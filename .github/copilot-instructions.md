# Instrucciones para GitHub Copilot - SAP2000 Automation Suite

Proyecto Python que automatiza CSI SAP2000 vía COM (`comtypes`) con GUI PySide6. Incluye integración con Microsoft Word para reportes.

## Arquitectura del Proyecto

```
main_app.py           # Punto de entrada - QMainWindow con pestañas
sap_interface.py      # Singleton de conexión SAP2000 (emite connectionChanged Signal)
<Modulo>/
  ├── backend.py      # Lógica pura (comtypes, sin PySide6)
  ├── *_gui.py        # Widget QWidget (recibe sap_interface)
  └── config.py       # Constantes y configuración (opcional)
API/                  # Documentación de referencia CSI OAPI
Reportes/library/     # Snippets JSON para generación de memorias
```

## Regla de Oro: Retornos de comtypes

La API de SAP2000 usa `ByRef`. En Python con comtypes, las funciones retornan **TUPLA** con todos los valores de salida + código de estado **al final**.

```python
# ✗ Incorrecto (estilo VBA/C#)
ret = SapModel.Func(param_in, param_out)
if ret != 0: ...

# ✓ Correcto (Python comtypes)
ret = SapModel.LoadCases.GetNameList()  # → (count, names_tuple, RetCode)
if ret[-1] == 0:  # RetCode siempre es el último
    count, names = ret[0], ret[1]
```

## Inyección de Dependencias

**Backend**: recibe `sap_model` en constructor, sin dependencias GUI.

```python
class MiBackend:
    def __init__(self, sap_model):
        self.SapModel = sap_model  # Puede ser None para tests

    def mi_tarea(self):
        if not self.SapModel: return None
        ret = self.SapModel.DatabaseTables.GetTableForDisplayArray(...)
        return ret[:-1] if ret[-1] == 0 else None
```

**GUI Widget**: recibe `sap_interface`, instancia backend bajo demanda.

```python
class MiWidget(QWidget):
    def __init__(self, parent=None, sap_interface=None):
        super().__init__(parent)
        self.sap_interface = sap_interface

    def on_action(self):
        backend = MiBackend(self.sap_interface.SapModel)
        backend.mi_tarea()
```

## Crear Nuevo Módulo

1. Crear carpeta `Nuevo_Modulo/` con `__init__.py`, `backend.py`, `*_gui.py`
2. Backend incluye `if __name__ == "__main__":` para pruebas standalone
3. GUI soporta ejecución aislada con fallback a `GetActiveObject`:
   ```python
   if __name__ == "__main__":
       app = QApplication(sys.argv)
       window = MiWidget()  # sap_interface=None → backend conecta solo
       window.show()
       sys.exit(app.exec())
   ```
4. Registrar en `main_app.py` → `init_tabs()` pasando `self.sap_interface`

## Pruebas de Módulos

```bash
# Backend aislado (conecta vía GetActiveObject)
python Nuevo_Modulo/backend.py

# GUI como módulo
python -m Nuevo_Modulo.gui
```

## Integración con Word (Reportes)

El módulo `Reportes/` usa `WordService` (comtypes → Word.Application):
- Ecuaciones: UnicodeMath nativo, no LaTeX. Ver `equation_translator.py`
- Símbolos: `\alpha` → `α`, `\sum` → `∑` (diccionario `UNICODEMATH_SYMBOLS`)
- Snippets: JSON en `Reportes/library/` con estructura `{category, snippets: [{id, title, content}]}`

## Convenciones

- Usar `self.SapModel` (mayúscula) para consistencia con API CSI
- Verificar `if not self.SapModel: return` al inicio de métodos backend
- Importaciones relativas en módulos: `from .backend import MiBackend`
- Referencia API: consultar archivos `.md` en `API/` (ej: `Load_Cases.md`, `Database_Tables.md`)
