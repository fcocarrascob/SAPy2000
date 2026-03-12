# Combinaciones de Carga

Módulo para lectura, edición matricial y escritura de **Load Combinations** en SAP2000 mediante una interfaz tipo spreadsheet.

## Descripción

Permite extraer todas las combinaciones de carga definidas en un modelo SAP2000 abierto, presentarlas en una tabla editable (filas = combos, columnas = load cases, celdas = scale factors), y empujar los cambios de vuelta al modelo. Soporta los tipos: Linear Add, Envelope, Absolute Add, SRSS y Range Add.

## Arquitectura

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `combos_backend.py` | `ComboBackend` | Lógica pura contra `SapModel` — lectura y escritura de combos vía API `RespCombo` |
| `app_combos_gui.py` | `CombosWidget` | Widget `QWidget` con `QTableWidget` dinámica, toolbar y lógica de presentación |

La inyección de dependencias sigue el patrón estándar del proyecto:

```python
# Backend recibe sap_model directamente
backend = ComboBackend(sap_interface.SapModel)

# GUI recibe sap_interface y crea el backend bajo demanda
widget = CombosWidget(parent, sap_interface=sap_interface)
```

## Diagrama de Procedimiento

```mermaid
flowchart TD
    subgraph GUI["CombosWidget (PySide6)"]
        A["Usuario hace clic en<br/><b>Read from SAP2000</b>"]
        E["Tabla QTableWidget se<br/>llena con datos"]
        F["Usuario edita tabla:<br/>• Cambiar factores<br/>• Agregar/eliminar filas<br/>• Cambiar tipo combo"]
        G["Usuario hace clic en<br/><b>Send to SAP2000</b>"]
        H["send_to_sap() recolecta<br/>datos de tabla → list[dict]"]
    end

    subgraph Backend["ComboBackend"]
        B["get_load_cases()"]
        C["get_combinations()"]
        I["push_combinations(combos_data)"]
    end

    subgraph SAP["SAP2000 API (comtypes)"]
        B1["SapModel.LoadCases<br/>.GetNameList()"]
        C1["SapModel.RespCombo<br/>.GetNameList()"]
        C2["Por cada combo:<br/>GetTypeOAPI() +<br/>GetCaseList()"]
        I1{"¿Combo existe?<br/>RespCombo.Add()"}
        I2["ret == 0 → combo nuevo<br/>Asignar tipo SetTypeOAPI()"]
        I3["ret != 0 → ya existe<br/>SetTypeOAPI() +<br/>_clear_combo_items()"]
        I4["Por cada case/factor:<br/>RespCombo.SetCaseList()<br/>→ verificar ret[-1] == 0"]
    end

    A --> B --> B1
    B1 -->|"(count, names, 0)"| E
    A --> C --> C1 --> C2
    C2 -->|"[{name, type, items}]"| E
    E --> F --> G --> H --> I
    I --> I1
    I1 -->|"ret == 0"| I2
    I1 -->|"ret != 0"| I3
    I2 --> I4
    I3 --> I4
    I4 -->|"Siguiente combo"| I1
    I4 -->|"Todos procesados"| J["Resumen: n combos<br/>creados/actualizados"]

    style GUI fill:#e8f4f8,stroke:#2196F3
    style Backend fill:#fff3e0,stroke:#FF9800
    style SAP fill:#fce4ec,stroke:#E91E63
```

### Detalle del flujo

1. **Lectura** — `get_load_cases()` obtiene los nombres de Load Cases para crear las columnas. `get_combinations()` itera sobre cada combo existente extrayendo su tipo (`GetTypeOAPI`) y los factores por caso (`GetCaseList`).
2. **Edición** — La tabla permite modificar scale factors, cambiar el tipo de combo vía `QComboBox`, y agregar/eliminar filas.
3. **Escritura** — `push_combinations()` intenta `RespCombo.Add()` para cada combo; si ya existe (ret ≠ 0), actualiza tipo y limpia items existentes con `DeleteCase()`, luego agrega cada case/factor con `SetCaseList()`.

## Uso en la GUI

La pestaña **"Combinaciones de Carga"** en `main_app.py` presenta:

- **Toolbar**: Read from SAP · Send to SAP · Add Row · Delete Row
- **Tabla**: Columnas dinámicas según Load Cases del modelo

## Ejecución Standalone

```bash
# GUI independiente (conecta vía GetActiveObject)
python Combinations_Carga/app_combos_gui.py

# Backend aislado (pruebas)
python Combinations_Carga/combos_backend.py
```

## Dependencias

- `comtypes` (indirecta vía `sap_model`)
- `PySide6` (GUI)

## Infraestructura Utilizada

- **StyledButton** — Botones con variantes (primary para leer, success para enviar)
- **LogWidget** — Log de operaciones con timestamp
- **check_ret_code** — Validación de retornos API SAP2000
- **AppLogger** — Logging en backend

## Ejecutar Standalone

```bash
python -m Combinations_Carga.app_combos_gui
```
