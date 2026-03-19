# Placa Base

Módulo para la generación automatizada de geometría FEA de **placas base** en SAP2000 — crea shell elements para la placa, alas y alma de columna, anillos de pernos (transición círculo → cuadrado) y opcionalmente anchor chairs.

## Descripción

A partir de las dimensiones de una columna tipo I, parámetros de la placa y coordenadas de pernos, el módulo genera automáticamente en SAP2000:

- **Propiedades de área** shell (PLACA_BASE, ALA, ALMA)
- **Sección Frame circular** para pernos de anclaje (ej: `BOLT_19`)
- **Geometría de columna** (alas superior/inferior + alma) como áreas de 4 puntos
- **Anillos de pernos** por cada centro de bolt: puntos en círculo → cuadrado interior → cuadrado exterior → ring meshes conectando las capas
- **Pernos Frame** — elemento Frame circular sólido desde cada centro hacia abajo (longitud = 8×diámetro)
- **Con silla de anclaje**: perno de 2 tramos (silla→placa + placa→fundación), con Body en silla (6 DOF) y Body en placa (UZ libre)
- **Sin silla**: perno de 1 tramo (placa→fundación, Body 6 DOF)
- **Apoyo Pin** en el nodo inferior de cada perno (fijo UX/UY/UZ, libre RX/RY/RZ)
- **Área de enlace** (link area) conectando los grupos de pernos
- **Subdivisión** de alas, alma y link area en los puntos de intersección con pernos
- **Anchor chairs** opcionales
- **TC Limits** (compresión = 0) en todos los Frames de pernos — pernos no resisten compresión
- **Módulo de balasto** (resorte de compresión en cara inferior) asignado a todas las áreas en z=0

## Arquitectura

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `placabase_backend.py` | `PlateConfig` | Dataclass con geometría completa (bolts, columna, placa, anchor, material perno). `from_json()` carga desde JSON |
| `placabase_backend.py` | `BasePlateBackend` | Lógica de generación: crea puntos, áreas, ring meshes, pernos Frame, Body constraints, Pin restraints y subdivisiones vía API SAP2000 |
| `app_placabase_gui.py` | `BasePlateWidget` | Formulario con 6 grupos de inputs + log de salida |
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
        P1B["<b>1b. Bolt Section</b><br/>PropFrame.SetCircle()<br/>BOLT_{dia}"]
        P2["<b>2. Geometría columna</b><br/>create_area_by_coord()<br/>× 4 áreas"]
        P3["<b>3. Loop por bolt_center</b>"]
        P3A["create_circle/square_points()"]
        P3E["create_ring_mesh() × 2"]
        P3CHAIR{"  ¿Silla de anclaje?"}
        P3YES["<b>CON SILLA</b><br/>create_single_chair()<br/>+ Frame silla→placa<br/>+ Frame placa→fundación<br/>+ Body silla (6 DOF)<br/>+ Body placa (UZ libre)<br/>+ Pin"]
        P3NO["<b>SIN SILLA</b><br/>Frame placa→fundación<br/>+ Body (6 DOF)<br/>+ Pin"]
        P4["<b>4. Link area</b><br/>conecta grupos de pernos"]
        P5["<b>5. Subdivisión</b><br/>alas + alma + link"]
        P6["<b>6. TC Limits</b><br/>Compresión=0 en pernos"]
        P7B["<b>7. Balasto</b><br/>Resorte en áreas z=0"]
        P8["View.RefreshView()"]
    end

    A --> A2
    A --> A3 --> A4 --> C1
    C1 --> C2 --> P1

    P1 --> P1B --> P2 --> P3
    P3 --> P3A --> P3E --> P3CHAIR
    P3CHAIR -->|"✅ Sí"| P3YES
    P3CHAIR -->|"❌ No"| P3NO
    P3YES -->|"Siguiente bolt"| P3
    P3NO -->|"Siguiente bolt"| P3
    P3YES -->|"Todos procesados"| P4
    P3NO -->|"Todos procesados"| P4
    P4 --> P5 --> P6 --> P7B --> P8

    style GUI fill:#e8f4f8,stroke:#2196F3
    style Config fill:#e8f5e9,stroke:#4CAF50
    style Backend fill:#fff3e0,stroke:#FF9800
```

### Detalle del flujo

| Paso | Acción | API SAP2000 |
|---|---|---|
| 1 | Crear propiedades shell con espesores diferentes | `PropArea.SetShell_1()` |
| 1b | Crear sección Frame circular para pernos | `PropFrame.SetCircle()` |
| 2 | Crear 4 áreas rectangulares para alas y alma | `AreaObj.AddByCoord()` |
| 3a | Generar puntos en círculo y cuadrados por perno | `PointObj.AddCartesian()` |
| 3b | Crear ring meshes (transición círculo→cuadrados) | `AreaObj.AddByPoint()` |
| 3c | **Con silla**: crear geometría de silla + Frame silla→placa | `create_single_chair()` + `FrameObj.AddByPoint()` |
| 3d | Crear Frame placa→fundación (L=8d) | `FrameObj.AddByPoint()` |
| 3e | Body Constraint en silla (6 DOF) o placa (6 DOF sin silla, UZ libre con silla) | `ConstraintDef.SetBody()` + `PointObj.SetConstraint()` |
| 3f | Asignar apoyo Pin al nodo inferior | `PointObj.SetRestraint()` |
| 4 | Crear área rectangular que conecta bolt groups | `AreaObj.AddByCoord()` |
| 5 | Subdividir áreas existentes por puntos de perno | `EditArea.Divide()` con selección |
| 6 | Placas anchor chair (opcional) | `AreaObj.AddByCoord()` |
| 7 | Asignar TC Limits: compresión = 0 en pernos Frame | `FrameObj.SetTCLimits()` |
| 8 | Seleccionar áreas en z=0 y asignar módulo de balasto | `SelectObj.CoordinateRange()` + `AreaObj.SetSpring()` con `ItemType=2` |

### Preset de posiciones de pernos

El widget incluye un generador automático (`generate_preset_positions()`) que calcula coordenadas de centros de pernos según:
- Número de pernos por fila
- Dimensiones de la columna (H, B)
- Espaciamientos predefinidos por diámetro de perno

## Configuración JSON

El archivo `placabase_ARA_config.json` almacena:

| Campo | Tipo | Descripción |
|---|---|---|
| `bolt_dia` | `float` | Diámetro del perno (mm) |
| `bolt_material` | `string` | Nombre del material para la sección Frame del perno (debe existir en el modelo SAP2000) |
| `H_col`, `B_col` | `float` | Dimensiones de la columna |
| `n_pernos` | `int` | Pernos por fila (para preset) |
| `bolt_centers` | `list` | Coordenadas `[x, y, z]` de cada centro |
| `flange_thickness`, `web_thickness`, `plate_thickness` | `float?` | Espesores (mm) |
| `ks_balasto` | `float?` | Módulo de balasto [kgf/cm³] (vacío = sin springs) |
| `include_anchor_chair` | `bool` | Toggle para silla de anclaje |
| `anchor_chair_height`, `anchor_chair_thickness` | `float?` | Dimensiones de la silla |

## Uso en la GUI

La pestaña **"Diseño Placa Base"** en `main_app.py` presenta:

1. **Column Profile** — H, B, espesores de ala y alma
2. **Base Plate** — Espesor de la placa
3. **Bolts** — Diámetro (ComboBox), tabla manual de centros X/Y, o generador preset
4. **Anchor Chair** — Toggle + dimensiones (opcional)
5. **Propiedades Adicionales** — Módulo de balasto ks (kgf/cm³)
6. **Output Log** — Mensajes de ejecución
7. **Preview** — Visualización en vivo del layout

## Ejecución Standalone

```bash
# Backend (requiere SAP2000 activo + placabase_ARA_config.json)
python Placa_Base/placabase_backend.py

# GUI independiente
python Placa_Base/app_placabase_gui.py
```

## Infraestructura Utilizada

- **StyledButton** — Botón "🏗️ Save & Execute" (success)
- **LogWidget** — Log de ejecución con timestamp
- **check_ret_code** — Validación de retornos API SAP2000
- **AppLogger** — Logging en backend

## Ejecutar Standalone

```bash
python -m Placa_Base.app_placabase_gui
```

## Dependencias

- `comtypes` (API SAP2000)
- `PySide6` (GUI)
- `json` (configuración)
- `math` (geometría)
