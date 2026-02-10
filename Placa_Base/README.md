# Placa Base

Módulo para la generación automatizada de geometría FEA de **placas base** en SAP2000 — crea shell elements para la placa, alas y alma de columna, anillos de pernos (transición círculo → cuadrado) y opcionalmente anchor chairs.

## Descripción

A partir de las dimensiones de una columna tipo I, parámetros de la placa y coordenadas de pernos, el módulo genera automáticamente en SAP2000:

- **Propiedades de área** shell (PLACA_BASE, ALA, ALMA)
- **Geometría de columna** (alas superior/inferior + alma) como áreas de 4 puntos
- **Anillos de pernos** por cada centro de bolt: puntos en círculo → cuadrado interior → cuadrado exterior → ring meshes conectando las capas
- **Área de enlace** (link area) conectando los grupos de pernos
- **Subdivisión** de alas, alma y link area en los puntos de intersección con pernos
- **Anchor chairs** opcionales

## Arquitectura

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `placabase_backend.py` | `PlateConfig` | Dataclass con geometría completa (bolts, columna, placa, anchor). `from_json()` carga desde JSON |
| `placabase_backend.py` | `BasePlateBackend` | Lógica de generación: crea puntos, áreas, ring meshes y subdivisiones vía API SAP2000 |
| `app_placabase_gui.py` | `BasePlateWidget` | Formulario con 5 grupos de inputs + log de salida |
| `app_placabase_gui.py` | `PreviewWidget` | Canvas custom (`paintEvent`) — dibuja sección I, bolt positions y contorno A×A |
| `placabase_ARA_config.json` | — | Configuración persistida (dimensiones, centros de pernos) |

> 📄 Para el detalle de bajo nivel de cada llamada COM, ver [docs/placabase_ARA_flow.md](docs/placabase_ARA_flow.md).

## Diagrama de Procedimiento

```mermaid
flowchart TD
    subgraph GUI["BasePlateWidget (PySide6)"]
        A["Usuario configura:<br/>• H_col, B_col, t_flange, t_web<br/>• Espesor placa base<br/>• Diámetro pernos + centros<br/>• Anchor chair (opcional)"]
        A2["PreviewWidget<br/>dibuja sección I +<br/>bolt positions en vivo"]
        A3["<b>Save & Execute</b>"]
        A4["Guarda placabase_ARA_config.json"]
    end

    subgraph Config["PlateConfig"]
        C1["PlateConfig.from_json()<br/>→ dataclass con geometría"]
        C2["map_dia_to_AB()<br/>bolt_dia → espaciamiento A/B"]
    end

    subgraph Backend["BasePlateBackend.run()"]
        P1["<b>1. Shell Properties</b><br/>PropArea.SetShell_1()<br/>× 3 (PLACA_BASE, ALA, ALMA)"]
        P2["<b>2. Geometría columna</b><br/>create_area_by_coord()<br/>× 4 áreas:<br/>flange top, flange bottom,<br/>web left, web right"]
        P3["<b>3. Loop por bolt_center</b>"]
        P3A["create_circle_points()<br/>PointObj.AddCartesian × N"]
        P3B["create_square_points()<br/>(inner square)"]
        P3C["create_square_points()<br/>(outer square)"]
        P3D["sort_points_angularly()<br/>+ align_rings()"]
        P3E["create_ring_mesh()<br/>circle ↔ inner square"]
        P3F["create_ring_mesh()<br/>inner ↔ outer square"]
        P4["<b>4. Link area</b><br/>create_area_by_coord()<br/>conecta grupos de pernos"]
        P5["<b>5. Subdivisión</b><br/>divide_area_by_selection()<br/>alas + alma + link en<br/>intersecciones con pernos"]
        P6["<b>6. Anchor chairs</b><br/>(si habilitado)<br/>create_area_by_coord()"]
        P7["View.RefreshView()"]
    end

    A --> A2
    A --> A3 --> A4 --> C1
    C1 --> C2 --> P1

    P1 --> P2 --> P3
    P3 --> P3A --> P3B --> P3C
    P3C --> P3D --> P3E --> P3F
    P3F -->|"Siguiente bolt_center"| P3
    P3F -->|"Todos procesados"| P4
    P4 --> P5 --> P6 --> P7

    style GUI fill:#e8f4f8,stroke:#2196F3
    style Config fill:#e8f5e9,stroke:#4CAF50
    style Backend fill:#fff3e0,stroke:#FF9800
```

### Detalle del flujo

| Paso | Acción | API SAP2000 |
|---|---|---|
| 1 | Crear propiedades shell con espesores diferentes | `PropArea.SetShell_1()` |
| 2 | Crear 4 áreas rectangulares para alas y alma | `AreaObj.AddByCoord()` |
| 3a | Generar N puntos equidistantes sobre círculo del perno | `PointObj.AddCartesian()` |
| 3b–c | Generar puntos de cuadrado interior y exterior | `PointObj.AddCartesian()` |
| 3d | Ordenar angularmente y alinear anillos | Lógica geométrica Python |
| 3e–f | Crear paneles de transición entre anillos consecutivos | `AreaObj.AddByPoint()` |
| 4 | Crear área rectangular que conecta bolt groups | `AreaObj.AddByCoord()` |
| 5 | Subdividir áreas existentes por puntos de perno | `EditArea.Divide()` con selección |
| 6 | Placas anchor chair (opcional) | `AreaObj.AddByCoord()` |

### Preset de posiciones de pernos

El widget incluye un generador automático (`generate_preset_positions()`) que calcula coordenadas de centros de pernos según:
- Número de pernos por fila
- Dimensiones de la columna (H, B)
- Espaciamientos predefinidos por diámetro de perno

## Uso en la GUI

La pestaña **"Diseño Placa Base"** en `main_app.py` presenta:

1. **Column Profile** — H, B, espesores de ala y alma
2. **Base Plate** — Espesor de la placa
3. **Bolts** — Diámetro (ComboBox), tabla manual de centros X/Y, o generador preset
4. **Anchor Chair** — Toggle + dimensiones (opcional)
5. **Output Log** — Mensajes de ejecución
6. **Preview** — Visualización en vivo del layout

## Ejecución Standalone

```bash
# Backend (requiere SAP2000 activo + placabase_ARA_config.json)
python Placa_Base/placabase_backend.py

# GUI independiente
python Placa_Base/app_placabase_gui.py
```

## Dependencias

- `comtypes` (API SAP2000)
- `PySide6` (GUI)
- `json` (configuración)
- `math` (geometría)
